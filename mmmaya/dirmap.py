from maya import cmds


def setup():
    print '[mmmaya.dirmap] Setting up dirmaps:'
    
    to_map = [

        # Original (pre-Linux) Windows to Linux.
        ('K:/', '/Volumes/CGroot'),
        ('Y:/', '/Volumes/PD01'),
        ('Z:/', '/Volumes/AnimationProjects'),

        # Old and new (2016-07-04) Miao Miao.
        ('//10.10.1.3/AnimationProjects', '/Volumes/AnimationProjects'),
        ('//10.10.1.5/AnimationProjects', '/Volumes/AnimationProjects'),

        # Modern (Shed projects) Windows to Linux.
        ('U:/', '/Volumes/CGroot'),

        # SitG: Mike's home to studio.
        ('/Volumes/heap/sitg/work/markmedia',      '/Volumes/CGroot/Projects/SitG'), # Old.
        ('/Volumes/heap/sitg/work/film',           '/Volumes/CGroot/Projects/SitG'), # Current.
        ('/Volumes/heap/sitg/work/artifacts-film', '/Volumes/CGartifacts/Projects/SitG'), # Current artifacts.

    ]

    # File from remote users should normalize back.
    for name in 'CGroot', 'CGartifacts':
        to_map.extend((
            ('/Volumes/{}.offline'.format(name), '/Volumes/{}'.format(name)),
            ('/Volumes/offline/{}'.format(name), '/Volumes/{}'.format(name)),
            ('/Volumes/{}.online'.format(name),  '/Volumes/{}'.format(name)),
        ))

    for src, dst in to_map:
        print '[mmmaya.dirmap]     Mapping %s to %s' % (src, dst)
        cmds.dirmap(m=(src, dst))
       
    cmds.dirmap(enable=True)
