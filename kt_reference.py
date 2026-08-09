from maya import cmds

# Load all reference nodes and every nested child
all_reference_nodes = cmds.ls(rf=True)

print(all_reference_nodes)


# Sort by hierarchy
all_reference_nodes.sort(key=len, reverse=False)

potential_orphaned_nodes = list()

for reference_node in all_reference_nodes:
	try:
		if not cmds.referenceQuery(reference_node, isLoaded=True):
			cmds.file(loadReference=reference_node)
			# We just loaded a new reference node that could have nested children, check for nests.
			children = cmds.referenceQuery(reference_node, referenceNode=True, child=True)
			if children:
				for child in children:
					# If they are not already in the list of nodes to load, add them.
					if child not in all_reference_nodes:
						all_reference_nodes.append(child)
				# Sort by hierarchy again
				all_reference_nodes.sort(key=len, reverse=False)
	except Exception as error:
		print("ERROR: Couldn't load ref node '{}' due to error: {}".format(reference_node, error))
		# This node is most likely an orphan, add to purge list
		potential_orphaned_nodes.append(reference_node)

# Purge orphaned nodes if any exist.
if potential_orphaned_nodes:
	for orphan in potential_orphaned_nodes:
		try:
			cmds.lockNode(orphan, lock=False)
			cmds.delete(orphan)
			print("Trying to delete orphaned node {}".format(orphan))
		except Exception as error:
			print("Couldn't delete orphaned node because of {}".format(error))