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


to_online = DirMap({
    '/Volumes/CGroot'        : '/Volumes/CGroot.online',
    '/Volumes/CGroot.offline': '/Volumes/CGroot.online',

})
to_offline = DirMap({
    '/Volumes/CGroot'       : '/Volumes/CGroot.offline',
    '/Volumes/CGroot.online': '/Volumes/CGroot.offline',
})



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
            if os.path.exists(offline):
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


def go_neutral(volume='CGroot'):
    base = os.path.join('/Volumes', volume)
    for ext in '', '.offline', '.online':
        src = base + ext
        dst = cmds.dirmap(getMappedDirectory=src)
        if dst:
            print 'Unmapping {} -> {}'.format(src, dst)
            cmds.dirmap(unmapDirectory=src)


def go_online():
    for name in 'CGroot', 'CGartifacts', 'EDsource':
        volume = os.path.join('/Volumes', name)
        go_neutral(volume)
        cmds.dirmap(mapDirectory=(volume, volume + '.online'))
        cmds.dirmap(mapDirectory=(volume + '.offline', volume + '.online'))
    print 'Please reopen the scene!'


def go_offline():
    for name in 'CGroot', 'CGartifacts', 'EDsource':
        volume = os.path.join('/Volumes', name)
        go_neutral(volume)
        cmds.dirmap(mapDirectory=(volume, volume + '.offline'))
        cmds.dirmap(mapDirectory=(volume + '.online', volume + '.offline'))
    print 'Please reopen the scene!'

