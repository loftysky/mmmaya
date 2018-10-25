from __future__ import print_function

from subprocess import check_output
import argparse
import os
import re
import shlex

import memoize
from sgfs import SGFS

import pymel.core as pm

from ..abc.link import link, unlink


def dummy_progress(value=None, label=None, minimum=None, maximum=None):
    pass

def discover_caches(progress=dummy_progress, sgfs=None):

    sgfs = sgfs or SGFS()
    sg = sgfs.session

    workspace = pm.workspace.getcwd()
    shot = sgfs.entity_from_path(workspace, ['Shot'])
    anim_tasks = sg.find('Task', [
        ('entity', 'is', shot),
        ('step.Step.short_name', 'is', 'anim'),
    ])
    if len(anim_tasks) != 1:
        raise ValueError("Found {} anim tasks for {}.".format(len(anim_tasks), shot))
    anim_task = anim_tasks[0]
    anim_path = sgfs.path_for_entity(anim_task)

    abc_dir = os.path.join(anim_path, 'maya', 'cache', 'alembic')
    available = []
    for name in sorted(os.listdir(abc_dir)):
        abc_path = os.path.join(abc_dir, name)

        print(abc_path)

        raw_info = check_output(['abcls', '-lm', abc_path])
        raw_info = re.sub('\x1b\\[[\\d;]*[a-zA-Z]', '', raw_info)

        scene_path = None
        nodes_by_namespace = {}
        for i, line in enumerate(raw_info.splitlines()):

            line = line.rstrip()
            if not line:
                continue

            is_header = line[0].isspace()
            is_body = i and not is_header

            if is_header:
                if line.strip().startswith('user description'):
                    m = re.search(r'Exported from: (.+?)$', line)
                    if not m:
                        raise ValueError("Could not parse description {!r}.".format(line))
                    scene_path = m.group(1)
                    print('    scene_path: {}'.format(scene_path))

            elif is_body:
                m = re.match(r'(?:Abc\w+)\s+([\w:]+)(?:\s|$)', line)
                if not m:
                    raise ValueError("Could not parse line {!r}.".format(line))
                node = m.group(1)
                if ':' not in node:
                    raise ValueError("Node {!r} has no namespace.".format(node))
                namespace, _ = node.split(':', 1)
                nodes_by_namespace.setdefault(namespace, []).append(node)

        if not scene_path:
            raise ValueError("Did not find scene path in description.")

        print('    namespaces: {}'.format(', '.join(sorted(nodes_by_namespace))))
        available.append((abc_path, scene_path, nodes_by_namespace))

    return available


file_command_parser = argparse.ArgumentParser()
file_command_parser.add_argument('-dr')
file_command_parser.add_argument('-ns')
file_command_parser.add_argument('-op')
file_command_parser.add_argument('-r', action='store_true')
file_command_parser.add_argument('-rdi')
file_command_parser.add_argument('-rfn')
file_command_parser.add_argument('-typ')
file_command_parser.add_argument('path')

def parse_references(scene):

    if not scene.endswith('.ma'):
        raise ValueError("Scene is not MayaAcii; {!r}.".format(scene))

    '''The files tend to look like:

    //Maya ASCII 2018ff08 scene
    //Name: Sq02_Sh140,anim,abcSetup,v0000,r0113.ma
    //Last modified: Wed, Oct 03, 2018 02:12:17 PM
    //Codeset: UTF-8
    file -rdi 1 -ns "GPM" -rfn "Rig_6RN" -typ "mayaAscii" "/Volumes/CGroot/Projects/ChangchunMovie/assets/characters/GenericPoliceMan/rig/published/maya_scene/Rig/v0009/GenericPoliceMan,rig,v0000,r0018.ma";
    file -rdi 1 -ns "GPM03_" -rfn "Rig_8RN" -typ "mayaAscii" "/Volumes/CGroot/Projects/ChangchunMovie/assets/characters/GenericPoliceMan03/rig/published/maya_scene/Rig/v0004/GenericPoliceMan03,rig,v0000,r0012.ma";
    file -rdi 1 -ns "GPM_1" -rfn "PLPo4_3RN" -typ "mayaAscii" "/Volumes/CGroot/Projects/ChangchunMovie/assets/characters/GenericPoliceMan/rig/published/maya_scene/Rig/v0009/GenericPoliceMan,rig,v0000,r0018.ma";
    file -rdi 1 -ns "GPM_" -rfn "PLPo2_1RN" -typ "mayaAscii" "/Volumes/CGroot/Projects/ChangchunMovie/assets/characters/GenericPoliceMan/rig/published/maya_scene/Rig/v0009/GenericPoliceMan,rig,v0000,r0018.ma";
    <snip>
    file -r -ns "GPM" -dr 1 -rfn "Rig_6RN" -typ "mayaAscii" "/Volumes/CGroot/Projects/ChangchunMovie/assets/characters/GenericPoliceMan/rig/published/maya_scene/Rig/v0009/GenericPoliceMan,rig,v0000,r0018.ma";
    file -r -ns "GPM03_" -dr 1 -rfn "Rig_8RN" -typ "mayaAscii" "/Volumes/CGroot/Projects/ChangchunMovie/assets/characters/GenericPoliceMan03/rig/published/maya_scene/Rig/v0004/GenericPoliceMan03,rig,v0000,r0012.ma";
    file -r -ns "GPM_1" -dr 1 -rfn "PLPo4_3RN" -typ "mayaAscii" "/Volumes/CGroot/Projects/ChangchunMovie/assets/characters/GenericPoliceMan/rig/published/maya_scene/Rig/v0009/GenericPoliceMan,rig,v0000,r0018.ma";
    file -r -ns "GPM_" -dr 1 -rfn "PLPo2_1RN" -typ "mayaAscii" "/Volumes/CGroot/Projects/ChangchunMovie/assets/characters/GenericPoliceMan/rig/published/maya_scene/Rig/v0009/GenericPoliceMan,rig,v0000,r0018.ma";
    <snip>
    requires maya "2018ff08";
    requires "mtoa" "3.0.0.2";
    requires -nodeType "AlembicNode" "AbcImport" "1.0";

    '''

    by_namespace = {}
    counts = {}

    with open(scene, 'rb') as fh:

        buffer_ = ''

        for line in fh:
            
            # Comments aren't terminated with ;.
            if line.startswith('//'):
                continue

            # Build up a buffer until we have full commands.
            buffer_ += line.rstrip()
            if not buffer_.endswith(';'):
                continue
            line = buffer_[:-1]
            buffer_ = ''

            parts = line.split(None, 1)
            if parts[0] in ('requires', 'fileInfo', 'currentUnit'):
                continue

            if parts[0] != 'file':
                break

            argv = shlex.split(line)[1:]
            args = file_command_parser.parse_args(argv)

            count = counts.get(args.path, 0)
            counts[args.path] = count + 1

            by_namespace.setdefault(args.ns, (args.path, count))

    return by_namespace


def pick_todo(available, sgfs=None):

    sgfs = sgfs or SGFS()
    sg = sgfs.session

    memo = memoize.Memoizer({})

    @memo
    def get_anim_references(anim_scene):
        return parse_references(anim_scene)

    @memo
    def get_reference(references, namespace):

        try:
            return references[namespace][0]
        except KeyError:
            pass

        # We need to pretend the namespace button was pressed.
        path_to_asset = {path: get_rig_asset(path) for path, _ in references.values()}
        sg.fetch(path_to_asset.values(), ['sg_default_reference_namespace'])

        for used_namespace, (path, count) in references.items():
            asset = path_to_asset[path]
            ideal_namespace = asset['sg_default_reference_namespace']
            if count:
                ideal_namespace += '_{}'.format(count)
            if namespace == ideal_namespace:
                print("    WARNING: Namespace in scene {!r} assumed exported as {!r}.".format(used_namespace, ideal_namespace))
                return path

        raise ValueError("Could not resolve namespace {!r}.".format(namespace))

    @memo
    def get_rig_asset(rig_scene):
        return sgfs.entity_from_path(rig_scene, ['Asset'])

    # NOTE: PyMemoize is not as elegant as it could be here with these keys.
    @memo
    def get_asset_model_tasks(asset):
        tasks = sg.find('Task', [
            ('entity', 'is', asset),
            ('step.Step.short_name', 'is', 'model'),
        ])
        if not tasks:
            raise ValueError("Found {} model tasks for {}: {}.".format(len(tasks), asset, tasks))
        return tasks

    # NOTE: PyMemoize is not as elegant as it could be here with these keys.
    @memo
    def get_model_publish(model_task):

        publishes = []
        for task in model_tasks:
            publish = sg.find_one('PublishEvent', [
                    ('sg_link', 'is', task),
                    ('sg_type', 'is', 'maya_scene'),
                ], [
                    'sg_path',
                ],
                order=[
                    dict(field_name='created_at', direction='desc'),
                ]
            )
            if publish:
                publishes.append(publish)

        if len(publishes) != 1:
            raise ValueError("Found {} latest model publishes for {}.".format(len(publishes), model_tasks))

        return publishes[0]

    todo = []
    seen_namespaces = set()
    for abc_path, anim_scene, nodes_by_namespace in reversed(available):
        for namespace, nodes in sorted(nodes_by_namespace.iteritems()):

            if namespace in seen_namespaces:
                continue
            seen_namespaces.add(namespace)

            print(namespace)
            print('    abc_path:', abc_path)
            print('    anim_scene:', anim_scene)

            references = get_anim_references(anim_scene)
            rig_scene = get_reference(references, namespace)
            print('    rig_scene:', rig_scene)

            if rig_scene.endswith('.fbx'):
                print('    WARNING: Skippping FBX.')
                continue

            asset = get_rig_asset(rig_scene)
            print('    asset:', asset)
            
            # TODO: Do better.
            if asset['id'] == 1183:
                print('    WARNING: Skipping camera.')
                continue

            model_tasks = get_asset_model_tasks(asset)
            print('    model_tasks:', model_tasks)

            model_publish = get_model_publish(model_tasks)
            print('    model_publish:', model_publish)

            todo.append((namespace, model_publish, abc_path, nodes))

    return todo


def find_named_node(nodes, name):

    all_nodes = []
    for node in nodes:
        all_nodes.append(node)
        all_nodes.extend(pm.listRelatives(node, allDescendents=True, type='transform'))

    for node in all_nodes:
        if re.match(name, node.split(':')[-1]):
            return node


def assert_group_chain(*names):
    parent = None
    for name in names:
        try:
            node = pm.PyNode('{}|{}'.format(parent or '', name))
        except pm.MayaNodeError:
            if parent:
                node = pm.group(name=name, empty=True, parent=parent)
            else:
                node = pm.group(name=name, empty=True)
        parent = node
    return node

def assert_reference(namespace, path):

    model_group = assert_group_chain('animated', '{}_group'.format(namespace), 'model')

    existing = pm.getReferences()
    if namespace in existing:
        ref_node = existing[namespace]
        ref_path = ref_node.unresolvedPath()
        if ref_path != path:
            raise ValueError("Existing {!r} reference {!r} should be {!r}".format(
                namespace, ref_path, path,
            ))
        all_nodes = set(ref_node.nodes())
        nodes = []
        for node in all_nodes:
            if pm.nodeType(node) != 'transform':
                continue
            parents = pm.listRelatives(node, allParents=True)
            if not parents or all(p not in all_nodes for p in parents):
                nodes.append(node)

    else:
        before = set(pm.ls(assemblies=True))
        ref_node = pm.createReference(path,
            namespace=namespace,
        )
        if ref_node.namespace != namespace:
            raise ValueError("Could not create namespace {!r}; got {!r}.".format(namespace, ref_node.namespace))
        nodes = list(set(pm.ls(assemblies=True)) - before)

    for node in nodes:
        if model_group not in pm.listRelatives(node, allParents=True):
            pm.parent(node, model_group)

    return nodes


def assert_cache(namespace, path):

    cache_group = assert_group_chain('animated', '{}_group'.format(namespace), 'cache')

    pm.hide(cache_group)

    if not pm.hasAttr(cache_group, 'mmCachePath'):
        cache_group.addAttr('mmCachePath', dataType='string')

    nodes = pm.listRelatives(cache_group, children=True)
    if nodes:
        existing_path = cache_group.attr('mmCachePath').get()
        if not existing_path:
            raise ValueError("Cache group {} has children, but no mmCachePath set.".format(cache_group))
        if existing_path == path:
            print('    NOTE: Already up to date.')
            return nodes, True
        print('    WARNING: Out of date; deleting.')
        pm.delete(nodes)
        nodes = None

    if not nodes:
        before = set(pm.ls(assemblies=True))
        pm.AbcImport(path, ft='{}:[^:]*$'.format(namespace))
        nodes = list(set(pm.ls(assemblies=True)) - before)
        for node in nodes:
            pm.parent(node, cache_group)
        cache_group.attr('mmCachePath').set(path)

    return nodes, False


def merge(namespace, model_publish, cache_path, nodes):


    model_path = model_publish['sg_path']

    print(namespace)
    print("    reference:", model_path)
    model_nodes = assert_reference(namespace, model_path)

    model_root = find_named_node(model_nodes, 'hi')
    if not model_root:
        raise ValueError("Could not find model's 'hi' node.")
    print("    model_root:", model_root)

    print("    cache_path:", cache_path)
    cache_nodes, cache_is_current = assert_cache(namespace, cache_path)

    print("    cache_is_current:", cache_is_current)
    if not cache_is_current:
        cache_root = find_named_node(cache_nodes, 'hi')
        if not cache_root:
            raise ValueError("Could not find cache's 'hi' node.")
        print("    cache_root:", cache_root)
        unlink(model_root.longName()) # Just to be safe.
        link(cache_root.longName(), model_root.longName())



def run():
    sgfs = SGFS()
    available = discover_caches(sgfs=sgfs)
    print()
    todo = pick_todo(available, sgfs=sgfs)
    print()
    for x in sorted(todo):
        merge(*x)
        print()


