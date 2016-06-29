from maya import cmds


def setup():
	
	cmds.dirmap(m=('K:/', '/Volumes/CGroot'))
	cmds.dirmap(m=('Z:/', '/Volumes/AnimationProjects'))
	cmds.dirmap(enable=True)
