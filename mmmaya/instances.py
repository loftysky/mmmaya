import json
import os

from maya import cmds
import maya.OpenMaya as om1


IDENTITY = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def merge_as_instances_button():
    sel = cmds.ls(selection=True, long=True)
    if len(sel) < 2:
        cmds.error("Must select 2 objects")
        return

    for other in sel[1:]:
        merge_as_instances(sel[0], other)


def get_transform_and_mesh(node):

    type_ = cmds.nodeType(node)
    if type_ == 'transform':
        meshes = cmds.listRelatives(node, children=True, type='mesh', fullPath=True) or ()
        if len(meshes) != 1:
            raise ValueError('need single mesh', node, meshes)
        return node, meshes[0]

    if type_ == 'mesh':
        return cmds.listRelatives(node, parent=True, fullPath=True), node

    raise ValueError("node is not transform or mesh", node, type_)


def merge_as_instances(n1, n2):

    t1, s1 = get_transform_and_mesh(n1)
    t2, s2 = get_transform_and_mesh(n2)

    l1 = cmds.getAttr(s1 + '.v', size=True)
    l2 = cmds.getAttr(s2 + '.v', size=True)
    if l1 != l2:
        cmds.warning('mismatched geometry', l1, l2)
        return

    if s1.split('|')[-1] == s2.split('|')[-1]:
        cmds.warning('already instances: %s %s' % (n1, n2))
        return

    print s1, s2
    cmds.parent(s1, t2, add=True, shape=True)
    cmds.delete(s2)


def select_all_instances_button():

    instances = set()
    for node in cmds.ls(selection=True):
        name = node.split('|')[-1]
        for parent in cmds.listRelatives(node, allParents=True, fullPath=True):
            instances.add(parent + '|' + name)

    cmds.select(list(instances), replace=True)




def iter_dag():
    iter_ = om1.MItDag(om1.MItDag.kDepthFirst, om1.MFn.kInvalid)
    while not iter_.isDone():
        yield iter_.currentItem()
        iter_.next()


def deinstance():

    dag_fn = om1.MFnDagNode()
    dep_fn = om1.MFnDependencyNode()
    pdag_fn = om1.MFnDagNode()
    path_array = om1.MDagPathArray()

    seen = set()
    instances = []

    fh = open(os.path.expanduser('~/Desktop/instances.json'), 'w')

    for dag_obj in iter_dag():
        
        dag_fn.setObject(dag_obj)

        parent_count = dag_fn.instanceCount(False) # False -> direct instance, e.g. we have multiple parents.
        if parent_count == 1:
            continue

        path = dag_fn.fullPathName()
        if path in seen:
            continue
        seen.add(path)

        name = path.rsplit('|', 1)[-1]

        refed_parents = []
        parents = []
        for i in xrange(parent_count):
            pobj = dag_fn.parent(i)

            pdag_fn.setObject(pobj)
            parent = pdag_fn.fullPathName()

            dep_fn.setObject(pobj)
            if dep_fn.isFromReferencedFile():
                refed_parents.append(parent)
            else:
                parents.append(parent)

        # We can only deal with instances that are not references.
        if not parents:
            continue

        # The first referenced one may act as a parent, however!
        if refed_parents:
            parents.insert(0, refed_parents[0])

        instances.append((name, parents))

        # Write to the file.
        data = {'master': path}
        instances_data = data['instances'] = []
        for parent in parents[1:]:
            xform = cmds.xform(parent, q=True, worldSpace=True, matrix=True)
            xform = None if xform == IDENTITY else xform
            instances_data.append({'parent': parent, 'transform': xform})

        fh.write(json.dumps(data, sort_keys=True) + '\n')

    for name, parents in instances:

        print parents[0] + '|' + name
        for parent in parents[1:]:
            path = parent + '|' + name
            print '   ', path
        
            if cmds.nodeType(path) == 'transform':
                cmds.parent(path, removeObject=True)
            else:
                cmds.parent(path, removeObject=True, shape=True)


def reinstance():
        
    for line in open(os.path.expanduser('~/Desktop/instances.json')):
        all_data = json.loads(line.strip())
        
        master = all_data['master']
        is_transform = cmds.nodeType(master) == 'transform'
        
        for data in all_data['instances']:
            
            parent = data['parent']
            
            if not cmds.objExists(parent):
                parent = cmds.createNode('transform', name=parent.rsplit('|', 1)[-1])
                cmds.xform(parent, matrix=data['transform'], worldSpace=True)
            
            if is_transform:
                path = cmds.parent(master, parent, addObject=True)
            else:
                path = cmds.parent(master, parent, addObject=True, shape=True)
                
        