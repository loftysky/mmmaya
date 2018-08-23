
import maya.cmds as cmds

from sgfs import SGFS


def check_ref_namespaces():

    # Description : Python script runs through all the references within the maya scenes.
    # Checks they match the Shotgun defined Maya namespace, and renames
    # the incorrect namespaces.

    sgfs = SGFS()

    scene_references = cmds.file(query=True, reference=True) # finds all the reference paths in the scene
    scene_references.sort(reverse=True) #sorts them in reverse

    paths_and_assets = []
    assets = []

    # Collect all the assets so we can fetch them all at once.
    for path in scene_references:
        
        #info to query the maya namespace from the shotgun webpage
        assets = sgfs.entities_from_path(path, ['Asset'])
        if not assets:
            raise ValueError("No Asset entities for {}".format(path))
        asset = assets[0]

        paths_and_assets.append((path, asset))
        assets.append(asset)

    # Fetch them all in one call.
    sgfs.session.fetch(assets, ['sg_default_reference_namespace'])

    # Now that we have loaded all the asset namespaces, calculate what the
    # correct namespaces are.
    correct_namespaces = [] # (path, correct_namespace) tuples.
    for path, asset in paths_and_assets:

        #split is to find the duplicate number
        duplicate_number = path.split("{")
        duplicate_number = duplicate_number[-1].split("}")
        
        #if statement is to separate the first reference from the duplicates, because the first namespace will 
        #respect the maya namespace totally the duplicates will have a suffix "_#"
        if path == duplicate_number[0]:
            #query shotgun defined namespace
            correct_namespace = asset['sg_default_reference_namespace']  
            
        else:
            #query shotgun defined namespace + "_#"
            correct_namespace = asset['sg_default_reference_namespace'] + "_" + duplicate_number[0] 

        correct_namespaces.append((path, correct_namespace))


    # Make a few passes at changing namespaces until they are all fixed.
    # This is to deal with situations in which two references have each other's
    # namespace. Maya will let us attempt to set duplicate namespaces, but will
    # silently change it on us. So we just ask nicely a few times.
    for round_i in xrange(10):

        num_fixed = 0

        for path, correct_namespace in correct_namespaces:

            #query curent namespace
            current_namespace = cmds.file(path, query=1, namespace=True) 

            #renames namespace if it is incorrect
            if current_namespace != correct_namespace: 
                cmds.file(path, edit=1, namespace=correct_namespace)
                num_fixed += 1

        print "Fixed {} in round {}.".format(num_fixed, round_i)

        # Everything is fixed; bail!
        if not num_fixed:
            break

    else:
        raise ValueError("Could not fix all references after many attempts.")

