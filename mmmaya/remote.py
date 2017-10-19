from __future__ import absolute_import

import os
import shutil

from dirmap import DirMap

from maya import cmds


file_node_attributes = (
    ('audio',    'filename',        None,                                            None),
    ('file',     'fileTextureName', None,                                            None),
    ('reference', None,             lambda n: cmds.referenceQuery(n, filename=True), None),
    (None,        None,             lambda n: cmds.file(q=True, sceneName=True),     None),
)


to_online = {}
to_offline = {}

volume_names = ('CGroot', 'CGartifacts', 'EDsource')
for name in volume_names:

    bare = '/Volumes/{}'.format(name)
    online = '/Volumes/{}.online'.format(name)

    # Pick which style of offline we're using.
    offline_boot = '/Volumes/{}.offline'.format(name)
    offline_disk = '/Volumes/offline/{}'.format(name)
    if os.path.exists(offline_disk):
        offline = offline_disk
    else:
        offline = offline_boot

    to_online[bare] = online
    to_online[offline_boot] = online
    to_online[offline_disk] = online

    to_offline[bare] = offline
    to_offline[online] = offline

to_online = DirMap(to_online)
to_offline = DirMap(to_offline)


def make_offline_copies():

    for node_type, attr_name, getter, setter in file_node_attributes:

        nodes = cmds.ls(type=node_type) if node_type else [None]
        if not nodes:
            print 'No {} nodes.'.format(node_type)
            continue

        for node in nodes:

            raw_path = getter(node) if getter else cmds.getAttr(node + '.' + attr_name)
            online = to_online(raw_path)
            print node_type, node, attr_name, online

            if not os.path.exists(online):
                print 'WARNING: {} does not exist!'.format(online)
                continue

            offline = to_offline(raw_path)
            if offline == online or os.path.exists(offline):
                continue

            dir_ = os.path.dirname(offline)
            if not os.path.exists(dir_):
                os.makedirs(dir_)

            tmp = offline + '.tmp-' + os.urandom(2).encode('hex')
            try:
                shutil.copyfile(online, tmp)
                os.rename(tmp, offline)
            except Exception:
                os.unlink(tmp)
                raise


def install_dirmap(map_):
    for src, dst in sorted(map_.iteritems()):
        print 'Mapping', src, '->', dst
        existing = cmds.dirmap(getMappedDirectory=src)
        if existing and existing != dst:
            print '    was', existing
            cmds.dirmap(unmapDirectory=src)
        cmds.dirmap(mapDirectory=(src, dst))

def go_neutral():
    for map_ in (to_online, to_offline):
        for src in sorted(map_):
            dst = cmds.dirmap(getMappedDirectory=src)
            if dst:
                print 'Unmapping {} -> {}'.format(src, dst)
                cmds.dirmap(unmapDirectory=src)

def go_online():
    install_dirmap(to_online)
    print 'Please reopen the scene!'

def go_offline():
    install_dirmap(to_offline)
    print 'Please reopen the scene!'

