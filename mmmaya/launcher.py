import os
import shutil
import sys
import tempfile

from appinit.apps.core import iter_installed_apps
import sitetools.environ

from . import renderman
from .utils import Environ


def mktemp_app_dir(version):
	"""Build a minimal version of the user's MAYA_APP_DIR.
	
	The caller should delete it once done.

	We do this at all because we are having a pile of segfaults on the farm
	due to being unable to load something within `synColor` in the MAYA_APP_DIR.
	So lets just relocate it.

	"""

	version = str(version)
	new = tempfile.mkdtemp('maya_app_dir')
	new = os.path.join(new, version)
	os.makedirs(new)

	if sys.platform.startswith('linux'):
		old = os.path.expanduser('~/maya')
	else:
		old = os.path.expanduser('~/Library/Preferences/Autodesk/maya')
	old = os.path.join(old, version)

	env_path = os.path.join(old, 'Maya.env')
	if os.path.exists(env_path):
		shutil.copy(env_path, os.path.join(new, 'Maya.env'))

	return new


def main(render=False, python=False):

	import argparse

	# This is a bad hack to detect if we are running under Deadline's MayaBatch plugin.
	deadline_batch_plugin = '-prompt' in sys.argv

	parser = argparse.ArgumentParser(add_help=not (render or python))
	parser.set_defaults(background=False, python=python, render=render)
	if not (render or python or deadline_batch_plugin):
		parser.add_argument('-b', '--background', action='store_true')
		parser.add_argument('-p', '--python', action='store_true')
		parser.add_argument('-R', '--render', action='store_true')
	args, more_args = parser.parse_known_args()

	version = os.environ.get('MM_MAYA_VERSION', '2016')

	app = next(iter_installed_apps('maya==%s' % version), None)
	if not app:
		print >> sys.stderr, 'Could not find Maya', version
		exit(1)

	if args.render:
		command = app.get_command()
		dir_, name = os.path.split(command[-1])
		command[-1] = os.path.join(dir_, 'Render')
	else:
		command = None

	env = Environ(os.environ)

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
	env['PYTHONPATH'] = '%s:%s' % (
		app.get_site_packages(),
		env.get('PYTHONPATH', ''),
	)
	
	renderman.setup_env(version, env)

	if args.render:
		app_dir = mktemp_app_dir(version) # We need a clean MAYA_APP_DIR.
		try:
			env['MAYA_APP_DIR'] = app_dir
			proc = app.popen(more_args, command=command, env=env)
			proc.wait()
		finally:
			shutil.rmtree(app_dir)

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
