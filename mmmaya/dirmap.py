from maya import cmds


def setup():
	print '[mmmaya.dirmap] Setting up dirmaps:'
	for src, dst in [

		# Windows to Linux.
		('K:/', '/Volumes/CGroot'),
		('Z:/', '/Volumes/AnimationProjects'),

		# Old and new (July 4th) Miao Miao.
		('//10.10.1.3/AnimationProjects', '/Volumes/AnimationProjects'),
		('//10.10.1.5/AnimationProjects', '/Volumes/AnimationProjects'),

	]:
		print '[mmmaya.dirmap]     Mapping %s to %s' % (src, dst)
		cmds.dirmap(m=(src, dst))
	cmds.dirmap(enable=True)
