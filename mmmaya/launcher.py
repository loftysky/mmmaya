import os
import sys

from appinit.apps.core import iter_installed_apps


def main(render=False, python=False):

	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('-b', '--background', action='store_true')
	if not (render or python):
		parser.add_argument('-p', '--python', action='store_true')
		parser.add_argument('-R', '--render', action='store_true')
	args, more_args = parser.parse_known_args()

	app = next(iter_installed_apps('maya==2016'), None)
	if not app:
		print >> sys.stderr, 'Could not find Maya 2016'
		exit(1)

	if render or args.render:
		command = app.get_command()
		dir_, name = os.path.split(command[-1])
		command[-1] = os.path.join(dir_, 'Render')
	else:
		command = None

	env = os.environ.copy()

	# Disable the Autodesk "Customer Involvement Program", because it segfaults
	# when running on the farm (e.g. Deadline or Qube), and because the concept
	# is somewhat obnoxious.
	env['MAYA_DISABLE_CIP'] = '1'

	# Lets also disable the "Customer Error Reporting", because I don't feel
	# like accidentally sending arbitrary information.
	env['MAYA_DISABLE_CER'] = '1'


	app.exec_(more_args,
		command=command,
		env=env,
		python=python or args.python,
		background=args.background,
	)


def main_render():
	main(render=True)

def main_python():
	main(python=True)
