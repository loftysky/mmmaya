

def check_ref_namespaces():
	#written by Kevin Zimny
	#last updated 2018/08/15
	#Description : Python script runs through all the references within the maya scenes.
	#Checks they match the Shotgun defined Maya namespace, and renames
	#the incorrect namespaces.

	import maya.cmds as cmds
	from sgfs import SGFS
	sgfs = SGFS()

	SceneReferences = cmds.file(query=True, reference = True) #finds all the reference paths in the scene
	SceneReferences.sort (reverse = True) #sorts them in reverse

	for all in SceneReferences:
	    
	    #split is to find the duplicate number
	    DuplicateNumber = all.split("{")
	    DuplicateNumber = DuplicateNumber[-1].split("}")
	    
	    #info to query the maya namespace from the shotgun webpage
	    path = all
	    sgfs.entities_from_path(path)
	    sgfs.entities_from_path(path, ['Asset'])
	    assets = sgfs.entities_from_path(path, ['Asset'])
	    asset = assets[0]
	    asset.get('sg_default_reference_namespace')
	    
	    #if statement is to separate the first reference from the duplicates, because the first namespace will 
	    #respect the maya namespace totally the duplicates will have a suffix "_#"
	    if all == DuplicateNumber[0]:
	        
	        #query curent namespace
	        CurrentNamespace = cmds.file( path, query=1, namespace=True) 
	        #query shotgun defined namespace
	        CorrectNamespace = asset.fetch('sg_default_reference_namespace') 
	        #renames namespace if it is incorrect
	        if CurrentNamespace != CorrectNamespace : 
	            cmds.file( path, edit=1, namespace=CorrectNamespace) 
	        
	    else :
	        
	        #query curent namespace
	        CurrentNamespace = cmds.file( path, query=1, namespace=True) 
	        #query shotgun defined namespace + "_#"
	        CorrectNamespace = CorrectNamespace = asset.fetch('sg_default_reference_namespace')+"_"+DuplicateNumber[0] 
	        #renames namespace if it is incorrect
	        if CurrentNamespace != CorrectNamespace :
	            cmds.file( path, edit=1, namespace=CorrectNamespace)  