from maya import cmds


def mmmaya_windows_dirmap():
	print '[mmmaya.windows] Setting up dirmaps: for CGroot -> K and AnimationProjects -> Z'
	for letter, path in [
		('K:/', '/Volumes/CGroot'),
		('Z:/', '/Volumes/AnimationProjects'),
	]:
		print '[mmmaya.windows]     Mapping %s to %s' % (letter, path)
		cmds.dirmap(m=(path, letter))
	cmds.dirmap(enable=True)

mmmaya_windows_dirmap()
