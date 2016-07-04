from maya import cmds


def mmmaya_windows_dirmap():
	print '[mmmaya.windows] Setting up dirmaps: for CGroot -> K and AnimationProjects -> Z'
	for src, dst in [

		# Linux to Windows.
		('/Volumes/CGroot', 'K:/'),
		('/Volumes/AnimationProjects', 'Z:/'),

		# Miao Miao moved on July 4th.
		('//10.10.1.5/AnimationProjects', '//10.10.1.3/AnimationProjects'),

	]:
		print '[mmmaya.windows]     Mapping %s to %s' % (src, dst)
		cmds.dirmap(m=(src, dst))
	cmds.dirmap(enable=True)

mmmaya_windows_dirmap()


def mmmaya_check():
	print '[mmmaya.windows] Loaded OK!'
