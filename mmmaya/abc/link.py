from maya import cmds


def _name(path):
    return path.rsplit('|', 1)[-1].rsplit(':', 1)[-1]


def collect_by_name(root_node, res=None, **kwargs):

    res = {}

    for node in cmds.listRelatives(root_node, allDescendents=True, fullPath=True, **kwargs):
        print node
        res.setdefault(_name(node), node)

    return res





def link_button():


    sel = cmds.ls(selection=True) or ()
    if len(sel) != 2:
        cmds.error('Must have 2 objects selected.')
        
    srcs = collect_by_name(sel[0], type='mesh')
    dsts = collect_by_name(sel[1], type='mesh')

    for name, src_node in sorted(srcs.iteritems()):
        dst_node = dsts.get(name)
        if not dst_node:
            continue

        print name, src_node, dst_node

        src_transform = cmds.listRelatives(src_node, parent=True, path=True)[0]
        dst_transform = cmds.listRelatives(dst_node, parent=True, path=True)[0]

        # TODO: Check that src is even deforming first.
        transfer = cmds.transferAttributes(src_transform, dst_transform,
            afterReference=1,
            transferPositions=1,
            transferNormals=1,
            sampleSpace=4, # 4 == components
        )[0]

        print '   ', transfer


    srcs = collect_by_name(sel[0], type='transform')
    dsts = collect_by_name(sel[1], type='transform')

    for name, src_node in sorted(srcs.iteritems()):
        dst_node = dsts.get(name)
        if not dst_node:
            continue

        print name, src_node, dst_node

        # TODO: Do this with contraints.
        for attr in ('translate', 'rotate', 'scale', 'visibility'):
            connection = cmds.connectAttr(src_node + '.' + attr, dst_node + '.' + attr, force=True) 

        print '   ', connection



def unlink_button():

    sel = cmds.ls(selection=True) or ()
    if len(sel) != 1:
        cmds.error('Must have 1 object selected.')
    root = sel[0]


    for mesh in cmds.listRelatives(root, allDescendents=True, fullPath=True, type='mesh'):
        print mesh

        for node in cmds.listHistory(mesh):
            try:
                type_ = cmds.nodeType(node)
            except RuntimeError:
                continue
            if type_ != 'transferAttributes':
                continue
            print '   ', node
            cmds.delete(node)

    for xform in cmds.listRelatives(root, allDescendents=True, fullPath=True, type='transform'):
        print xform

        for src_attr in cmds.listConnections(xform, source=True, destination=False, plugs=True) or ():

            attr_name = src_attr.split('.')[-1]
            if attr_name not in ('translate', 'rotate', 'scale', 'visibility'):
                continue

            cmds.disconnectAttr(src_attr, xform + '.' + attr_name)


