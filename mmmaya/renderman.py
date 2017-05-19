import logging
import os
import sys


log = logging.getLogger(__name__)


def find_license(env=None):

    lic_path = env and env.get('PIXAR_LICENSE_FILE')
    if lic_path and os.path.exists(lic_path):
        return lic_path

    # Lets go looking for RenderMan.
    for lic_dir in (
        '/etc/mm/pixar',
        '/etc/mmconfig/pixar',
        '/Applications/Pixar',
        '/opt/pixar',
    ):
        lic_path = os.path.join(lic_dir, 'pixar.license')
        if os.path.exists(lic_path):
            log.info('Using license: %s', lic_path)
            return lic_path


def setup_env(maya_version, env):

    lic_path = find_license(env)
    if not lic_path:
        return

    rman_version = os.environ.get('MM_RENDERMAN_VERSION', '21.4')
    rms_slug = 'RenderManForMaya-%s-maya%s' % (rman_version, maya_version)
    rps_slug = 'RenderManProServer-%s' % rman_version
    for opt in (
        '/usr/local/mm/opt/pixar/renderman/%s' % rman_version,
        '/opt/pixar/',
        '/Applications/Pixar',
    ):
        rms_tree = os.path.join(opt, rms_slug)
        rman_tree = os.path.join(opt, rps_slug)
        if os.path.exists(rms_tree):
            if os.path.exists(rman_tree):
                log.info('Using RMSTREE: %s' % rms_tree)
                break
            else:
                log.warning('Found %s but no %s.' % (rms_tree, rman_tree))

    if not rms_tree:
        log.warning('Found %s but no %s.', lic_path, rms_slug)
        return

    env['RMSTREE'] = rms_tree
    env['RFMTREE'] = rms_tree # Not sure if this is used.
    env['RMANTREE'] = rman_tree
    env['PIXAR_LICENSE_FILE'] = lic_path

    env.append('MAYA_PLUG_IN_PATH', os.path.join(rms_tree, 'plug-ins')) # The shared library itself.
    env.append('MAYA_PLUG_IN_PATH', os.path.join(rms_tree, 'bin')) # Not sure if this is required.
    env.append('MAYA_SCRIPT_PATH', os.path.join(rms_tree, 'scripts')) # MEL for bootstrapping second load.
    env.append('PYTHONPATH', os.path.join(rms_tree, 'scripts')) # I thought this would be taken care of already...
    env.append('MAYA_RENDER_DESC_PATH', os.path.join(rms_tree, 'etc')) # For `Render -r rman`.
    env.append('XBMLANGPATH', os.path.join(rms_tree, 'icons') + ('/%B' if sys.platform.startswith('linux') else '')) # For shelf icons.

