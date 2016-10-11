import os
import sys

from appinit.apps.core import iter_installed_apps
import sitetools.environ


def main(render=False, python=False):

	import argparse

	# This is a bad hack to detect if we are running under Deadline's MayaBatch plugin.
	deadline_batch_plugin = '-prompt' in sys.argv

	parser = argparse.ArgumentParser()
	parser.set_defaults(background=False, python=python, render=render)
	if not (render or python or deadline_batch_plugin):
		parser.add_argument('-b', '--background', action='store_true')
		parser.add_argument('-p', '--python', action='store_true')
		parser.add_argument('-R', '--render', action='store_true')
	args, more_args = parser.parse_known_args()

	app = next(iter_installed_apps('maya==2016'), None)
	if not app:
		print >> sys.stderr, 'Could not find Maya 2016'
		exit(1)

	if args.render:
		command = app.get_command()
		dir_, name = os.path.split(command[-1])
		command[-1] = os.path.join(dir_, 'Render')
	else:
		command = None

	env = os.environ.copy()

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
