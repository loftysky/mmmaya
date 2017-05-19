from maya import cmds


def setup():
    print '[mmmaya.dirmap] Setting up dirmaps:'
    for src, dst in [

        # Windows to Linux.
        ('K:/', '/Volumes/CGroot'),
        ('Y:/', '/Volumes/PD01'),
        ('Z:/', '/Volumes/AnimationProjects'),

        # Old and new (2016-07-04) Miao Miao.
        ('//10.10.1.3/AnimationProjects', '/Volumes/AnimationProjects'),
        ('//10.10.1.5/AnimationProjects', '/Volumes/AnimationProjects'),

        # SitG: Mike's home to studio.
        ('/Volumes/heap/sitg/work/markmedia', '/Volumes/CGroot/Projects/SitG'), # Old.
        ('/Volumes/heap/sitg/work/film',      '/Volumes/CGroot/Projects/SitG'), # Current.

    ]:
        print '[mmmaya.dirmap]     Mapping %s to %s' % (src, dst)
        cmds.dirmap(m=(src, dst))
       
    cmds.dirmap(enable=True)
