
import maya.cmds as cmds

from sgfs import SGFS


def check_ref_namespaces():

    # Description : Python script runs through all the references within the maya scenes.
    # Checks they match the Shotgun defined Maya namespace, and renames
    # the incorrect namespaces.

    sgfs = SGFS()

    scene_references = cmds.file(query=True, reference=True) # finds all the reference paths in the scene
    scene_references.sort(reverse=True) #sorts them in reverse

    for _ in xrange(10):
        num_fixed = _fix_ref_namespacees(sgfs, scene_references)
        if not num_fixed:
            break
    else:
        raise ValueError("Could not fix all references after many attempts.")


def _fix_ref_namespacees(sgfs, scene_references):

    num_fixed = 0

    for path in scene_references:
        
        #split is to find the duplicate number
        duplicate_number = path.split("{")
        duplicate_number = duplicate_number[-1].split("}")
        
        #info to query the maya namespace from the shotgun webpage
        assets = sgfs.entities_from_path(path, ['Asset'])
        if not assets:
        	raise ValueError("No Asset entities for {}".format(path))
        asset = assets[0]
        
        #query curent namespace
        current_namespace = cmds.file(path, query=1, namespace=True) 

        #if statement is to separate the first reference from the duplicates, because the first namespace will 
        #respect the maya namespace totally the duplicates will have a suffix "_#"
        if path == duplicate_number[0]:
            #query shotgun defined namespace
            correct_namespace = asset.fetch('sg_default_reference_namespace')  
            
        else:
            #query shotgun defined namespace + "_#"
            correct_namespace = asset.fetch('sg_default_reference_namespace') + "_" + duplicate_number[0] 

        #renames namespace if it is incorrect
        if current_namespace != correct_namespace: 
            new_namespace = cmds.file(path, edit=1, namespace=correct_namespace)
            num_fixed += 1

    return num_fixed
