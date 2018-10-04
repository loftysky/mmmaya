from maya import cmds


def _name(path):
    return path.rsplit('|', 1)[-1].rsplit(':', 1)[-1]


def collect_by_name(root_node, **kwargs):

    # Start with the root.
    res = {_name(root_node): root_node}

    for node in cmds.listRelatives(root_node, allDescendents=True, fullPath=True, **kwargs):
        #print node
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

        # Only bother transferring attributes on meshes that have a connection
        # to an alembic node. This isn't a very strong connection, but it
        # seems to work for us.
        is_deformed = False
        for node in cmds.listHistory(src_node) or ():
            type_ = cmds.nodeType(node)
            if type_ == 'AlembicNode':
                is_deformed = True
                break
        if not is_deformed:
            continue

        print 'mesh {}: {} -> {}'.format(name, src_node, dst_node)

        src_transform = cmds.listRelatives(src_node, parent=True, path=True)[0]
        dst_transform = cmds.listRelatives(dst_node, parent=True, path=True)[0]

        transfer = cmds.transferAttributes(src_transform, dst_transform,
            afterReference=1, # To play nice with references.
            transferPositions=1,
            transferNormals=1,
            sampleSpace=4, # 4 == components
        )[0]

        print '    transferAttributes:', transfer


    srcs = collect_by_name(sel[0], type='transform')
    dsts = collect_by_name(sel[1], type='transform')

    for name, src_node in sorted(srcs.iteritems()):

        dst_node = dsts.get(name)
        if not dst_node:
            continue

        print 'transform {}: {} -> {}'.format(name, src_node, dst_node)


        is_alembiced = False
        if True:
            for node in cmds.listConnections(src_node, skipConversionNodes=True, source=True, destination=False) or ():
                if cmds.nodeType(node) == 'AlembicNode':
                    is_alembiced = True
                    print '    is alembiced:', node
                    break

        is_animated = False
        if True:
            for attr in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
                connections = cmds.listConnections('{}.{}'.format(src_node, attr), source=True, destination=False)
                if connections:
                    is_animated = True
                    print '    is animated: {} is connected'.format(attr)
                    break

        is_transformed = False
        if True:
            for attr in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
                src_value = cmds.getAttr('{}.{}'.format(src_node, attr))
                dst_value = cmds.getAttr('{}.{}'.format(dst_node, attr))
                if src_value != dst_value:
                    is_transformed = True
                    print '    is transformed: src {} {} != dst {}'.format(attr, src_value, dst_value)
                    break

        is_group = False
        if False:
            children = cmds.listRelatives(src_node)
            child_shapes = cmds.listRelatives(src_node, shapes=True)
            is_group = bool(children and not child_shapes)
            if is_group:
                print '    is group: {} children with no shapes'.format(len(children))

        do_constraint = is_alembiced or is_animated or is_transformed or is_group

        if do_constraint:

            # Bulk of transform is handled by a parent constraint...
            constraint = cmds.parentConstraint(src_node, dst_node, name='abc_link_parent_' + name)[0]
            print '    parentConstraint:', constraint
            constraint = cmds.scaleConstraint(src_node, dst_node, name='abc_link_scale_' + name)[0]
            print '    scaleConstraint:', constraint

        # We really do want to connect all the visibility regardless of animation.
        if name != 'hi':
            # ... and other attributed are done directly.
            for attr_name in ('visibility', ):
                cmds.connectAttr(src_node + '.' + attr_name, dst_node + '.' + attr_name, force=True)
                print '    {}: {} -> {}'.format(attr_name, src_node, dst_node)


def unlink_button():

    sel = cmds.ls(selection=True) or ()
    if len(sel) != 1:
        cmds.error('Must have 1 object selected.')
    root = sel[0]


    for mesh in cmds.listRelatives(root, allDescendents=True, fullPath=True, type='mesh'):
        
        print cmds.nodeType(mesh), mesh

        for node in cmds.listHistory(mesh):
        
            # At some point this didn't work for us...
            try:
                type_ = cmds.nodeType(node)
            except RuntimeError:
                print '    ** Could not get type of', node
                continue

            if type_ != 'transferAttributes':
                continue
            print '    transferAttributes:', node

            cmds.delete(node)

    for xform in cmds.listRelatives(root, allDescendents=True, fullPath=True, type='transform') or ():

        # Even though we ask for transforms, we get constraints, because
        # constraints inherit from transforms.
        if cmds.nodeType(xform) != 'transform':
            continue

        print 'transform', xform

        # Remove the parent constraints.
        for constraint_type in ('parentConstraint', 'scaleConstraint'):
            for node in set(cmds.listConnections(xform, source=True, destination=False, type=constraint_type) or ()):
                print '    {}: {}'.format(constraint_type, node)
                cmds.delete(node)

        # Remove attribute connections.
        connections = cmds.listConnections(xform, source=True, destination=False, type='transform', plugs=True, connections=True) or ()
        for i in xrange(0, len(connections), 2):

            dst_attr = connections[i] # The given object is returned first.
            src_attr = connections[i + 1]

            src_node, attr_name  = src_attr.split('.')
            dst_node, attr_name2 = dst_attr.split('.')
            if attr_name != attr_name2:
                continue

            # We remove a few too many connections here, because the development
            # versions of this transfered transforms via attribute connections.
            if attr_name not in ('translate', 'rotate', 'scale', 'visibility'):
                continue

            print '    {}: {} -> {}'.format(attr_name, src_node, dst_attr.split('.')[0])
            cmds.disconnectAttr(src_attr, xform + '.' + attr_name)


