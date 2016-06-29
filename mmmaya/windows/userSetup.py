import urllib
import sys
import os

def mmmaya_windows_setup():

	if sys.platform != 'win32' and not os.environ.get('MMMAYA_WINDOWS_FORCE'):
		print '[mmmaya.windows] WARNING: You are not on Windows; this script will not run.'
		return

	dir_ = os.path.expanduser('~/Documents/maya/scripts')

	res = urllib.urlopen('http://10.10.1.60/pipeline/mmmaya/raw/master/mmmaya/windows/userSetup2.py')
	if res.getcode() != 200:
		print '[mmmaya.windows] ERROR: Cannot bootstrap userSetup2.py due to HTTP', res.getcode()
		return

	path = os.path.join(dir_, 'userSetup2.py')
	with open(path, 'w') as fh:
		fh.write(res.read())

	print '[mmmaya.windows] Running userSetup2.py'
	execfile(path)

mmmaya_windows_setup()

