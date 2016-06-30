from maya import cmds


def setup():
	print '[mmmaya.dirmap] Setting up dirmaps:'
	for letter, path in [
		('K:/', '/Volumes/CGroot'),
		('Z:/', '/Volumes/AnimationProjects'),
	]:
		print '[mmmaya.dirmap]     Mapping %s to %s' % (letter, path)
		cmds.dirmap(m=(letter, path))
	cmds.dirmap(enable=True)
