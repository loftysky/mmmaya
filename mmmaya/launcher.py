import os
import sys

from appinit.apps.core import iter_installed_apps


def main(render=False):

	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('-p', '--python', action='store_true')
	parser.add_argument('-b', '--background', action='store_true')
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

	app.exec_(more_args, command=command, python=args.python, background=args.background)


def main_render():
	main(render=True)
