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

        transfer = cmds.transferAttributes(src_transform, dst_transform, afterReference=1, transferPositions=1, transferNormals=1, sampleSpace=4)[0]
        print '   ', transfer


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

    #     for node in cmds.listConnections(mesh, type='transferAttributes') or ():
    #         print '   ', node
    #         cmds.delete(node)
