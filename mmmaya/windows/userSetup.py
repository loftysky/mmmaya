import urllib
import sys
import os


def mmmaya_windows_setup():

	if sys.platform != 'win32' and not os.environ.get('MMMAYA_WINDOWS_FORCE'):
		print '[mmmaya.windows] WARNING: You are not on Windows; this script will not run.'
		return

	# Can't use os.path.expanduser here, because Maya adds "Documents" for some reason.
	dir_ = 'C:/Users/%s/Documents/maya/scripts' % os.environ['USERNAME']

	res = urllib.urlopen('http://10.10.1.60/pipeline/mmmaya/raw/master/mmmaya/windows/userSetup2.py')
	if res.getcode() != 200:
		print '[mmmaya.windows] ERROR: Cannot bootstrap userSetup2.py due to HTTP', res.getcode()
		return

	print '[mmmaya.windows] Bootstrapping userSetup2.py'
	path = os.path.join(dir_, 'userSetup2.py')
	with open(path, 'w') as fh:
		fh.write(res.read())

	print '[mmmaya.windows] Running userSetup2.py'
	execfile(path)

mmmaya_windows_setup()


def mmmaya_check():
	print '[mmmaya.windows] WARING: Bootstrap did not load.'
