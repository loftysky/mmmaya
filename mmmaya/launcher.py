import sys

from appinit.apps.core import iter_installed_apps


def main():

	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('-p', '--python', action='store_true')
	parser.add_argument('-b', '--background', action='store_true')
	parser.add_argument('args', nargs='*')
	args = parser.parse_args()

	app = next(iter_installed_apps('maya==2016'), None)
	if not app:
		print >> sys.stderr, 'Could not find Maya 2016'
		exit(1)

	app.exec_(args.args, python=args.python, background=args.background)
