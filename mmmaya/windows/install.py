import urllib
import sys
import os

if sys.platform != 'win32':
	print 'WARNING: You are not on Windows, and should not be installing this.'
	if not (os.environ.get('MMMAYA_WINDOWS_FORCE') or raw_input('Continue? (yes/no): ').strip().lower().startswith('y')):
		exit(1)

# Can't use os.path.expanduser here, because Maya adds "Documents" for some reason
# (and this might be running within a Maya).
dir_ = 'C:/Users/%s/Documents/maya/scripts' % os.environ['USERNAME']

if not os.path.exists(dir_):
	os.makedirs(dir_)

res = urllib.urlopen('http://10.10.1.60/pipeline/mmmaya/raw/master/mmmaya/windows/userSetup.py')
if res.getcode() != 200:
	print 'ERROR: HTTP', res.getcode()
	exit(2)

with open(os.path.join(dir_, 'userSetup.py'), 'w') as fh:
	fh.write(res.read())

print 'Installed userSetup.py'

