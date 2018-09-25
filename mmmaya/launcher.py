import os
import shutil
import sys
import tempfile

import pkg_resources

from appinit.apps.core import iter_installed_apps
import sitetools.environ

from .utils import Environ


def mktemp_app_dir(version):
    """Build a minimal version of the user's MAYA_APP_DIR.
    
    The caller should delete it once done.

    We do this at all because we are having a pile of segfaults on the farm
    due to being unable to load something within `synColor` in the MAYA_APP_DIR.
    So lets just relocate it.

    """

    version = str(version)
    root = tempfile.mkdtemp('maya_app_dir')
    new = os.path.join(root, 'maya')

    if sys.platform.startswith('linux'):
        old = os.path.expanduser('~/maya')
    else:
        old = os.path.expanduser('~/Library/Preferences/Autodesk/maya')

    try:
        shutil.copytree(old, new, ignore=shutil.ignore_patterns(
            'FBX',
            'mayaLog', # Junk.
            'mayaRenderLog.txt', # Junk.
            'presets', # Sometimes heavy.
            'projects', # Sometimes heavy.
            'synColor', # The important one.
        ))
    except shutil.Error as e:
        errs = e.args[0]
        print >> sys.stderr, "There were {} errors while creating MAYA_APP_DIR:".format(len(errs))
        for src, dst, why in errs:
            print >> sys.stderr, '{}\n\tsrc: {}\n\tdst: {}'.format(why, src, dst)

    return root, new


def check_adlm_resource_perms(fix=False):
    """Assert permissions on AdlmIntRes.xml are correct.

    Autodesk licensing will create a AdlmIntRes.xml temp file
    that is only readable by the current user, but that file is required
    for Arnold to license on the farm, AND the error handling in the
    client is terrible.

    This function checks, and optionally fixes those permissions.

    """

    # Via strace, we found maya.bin in a busy loop checking the file in /usr/tmp.
    # But /usr/tmp was a symlink to /var/tmp... and we don't mind being overly
    # cautious here.
    for tmp_dir in ('/var/tmp', '/usr/tmp', tempfile.gettempdir()):

        if not os.path.exists(tmp_dir):
            continue

        adlm_xml_path = os.path.join(tmp_dir, 'AdlmIntRes.xml')
        if os.path.exists(adlm_xml_path):
            
            perms = os.stat(adlm_xml_path).st_mode
            if perms & 0o444 == 0o444:
                continue

            if fix:
                try:
                    os.chmod(adlm_xml_path, 0o666)
                except OSError as e:
                    print >> sys.stderr, "[mmmaya.launcher] ERROR: {} could not have its permissions fixed; {}".format(adlm_xml_path, e)

            else:
                print >> sys.stderr, "[mmmaya.launcher] WARNING: {} has bad permissions (0o{:03o}), and this render may block.".format(
                    adlm_xml_path,
                    perms & 0o777,
                )


def main(render=False, python=False, version=os.environ.get('MMMAYA_VERSION', '2016')):

    import argparse

    # This is a bad hack to detect if we are running under Deadline's MayaBatch plugin.
    deadline_batch_plugin = '-prompt' in sys.argv

    parser = argparse.ArgumentParser(add_help=not (render or python))
    parser.set_defaults(background=False, python=python, render=render)
    parser.add_argument('-V', '--version', default=version)
    parser.add_argument('--verbose', action='count',
            help="Print debugging messages from the launcher.")
    parser.add_argument('-R', '--render-setup',
        help='''"on" for new "render setup", "off" for legacy "render layers"''')

    parser.add_argument('--dump-environ', action='store_true')

    if not (render or python or deadline_batch_plugin):
        parser.add_argument('--background', action='store_true')
        parser.add_argument('--python', action='store_true')
        parser.add_argument('--render', action='store_true')
    args, more_args = parser.parse_known_args()

    version = args.version

    app = next(iter_installed_apps('maya==%s' % args.version), None)
    if not app:
        print >> sys.stderr, 'Could not find Maya', args.version
        exit(1)

    if args.render:
        command = app.get_command()
        dir_, name = os.path.split(command[-1])
        command[-1] = os.path.join(dir_, 'Render')
    else:
        command = None

    env = Environ(os.environ)

    if args.render_setup:
        if args.render_setup.lower()   in ('on',  '1', 'true',  'enable',  'modern', 'new', 'setup'):
            env['MAYA_ENABLE_LEGACY_RENDER_LAYERS'] = '0'
        elif args.render_setup.lower() in ('off', '0', 'false', 'disable', 'legacy', 'old', 'layers'):
            env['MAYA_ENABLE_LEGACY_RENDER_LAYERS'] = '1'

    # Preserve the envvars for outside of the Maya environment.
    sitetools.environ.freeze(env, [
        'LD_LIBRARY_PATH',
        'DYLD_LIBRARY_PATH',
        'PYTHONPATH',
        'PYTHONHOME',
    ])

    # Disable the Autodesk "Customer Involvement Program", because it segfaults
    # when running on the farm (e.g. Deadline or Qube), and because the concept
    # is somewhat obnoxious.
    env['MAYA_DISABLE_CIP'] = '1'

    # Lets also disable the "Customer Error Reporting", because I don't feel
    # like accidentally sending arbitrary information.
    env['MAYA_DISABLE_CER'] = '1'

    # Put Maya's site-packages at the front of the PYTHONPATH. This should
    # likely end up in appinit, but I'm not sure if I want to do that yet.
    env.prepend('PYTHONPATH', app.get_site_packages())

    # We have PySide installed, which messes with PySide2.
    # This is a hack until we can deal with this via other means (as macOS
    # also has this problem, but that PySide is installed via VEE).
    if int(args.version[:4]) >= 2018:
        env.remove('PYTHONPATH', '/usr/lib64/python2.7/site-packages', strict=False)
        env.remove('PYTHONPATH', '/usr/lib/python2.7/site-packages', strict=False)

    # Include our mel.
    #env['MAYA_SCRIPT_PATH'] = '%s:%s' % (
    #    env.get('MAYA_SCRIPT_PATH', ''),
    #    os.path.abspath(os.path.join(__file__, '..', 'mel')),
    #)

    for ep in pkg_resources.iter_entry_points('mmmaya_prelaunch'):
        func = ep.load()
        if args.verbose:
            print >> sys.stderr, "[mmmaya.launcher] Running prelaunch: {}".format(ep)
        func(env, version)

    if args.dump_environ:
        for k, v in sorted(env.iteritems()):
            print '{}={}'.format(k, v)
        return

    if args.render:

        check_adlm_resource_perms()

        tmp_root, app_dir = mktemp_app_dir(version) # We need a clean MAYA_APP_DIR.

        code = 1
        try:
            env['MAYA_APP_DIR'] = app_dir
            proc = app.popen(more_args, command=command, env=env)
            code = proc.wait()
        finally:
            shutil.rmtree(tmp_root)
        
        check_adlm_resource_perms(fix=True)
        exit(code)

    else:
        app.exec_(more_args,
            command=command,
            env=env,
            python=args.python,
            background=args.background,
        )


def main_render():
    main(render=True)

def main_python():
    main(python=True)


if __name__ == '__main__':
    main()


