import maya.cmds as mc

def bake_geo_clean(rigged_mesh):
    
    print(rigged_mesh)
    # 1. Duplicate the mesh (keeps shaders/UVs)
    # We strip namespaces for the new name to keep it clean
    short_name = rigged_mesh.split(":")[-1]
    baked_name = short_name + "_BAKED"
    
    # Duplicate returns a list, we take the first item
    new_mesh = mc.duplicate(rigged_mesh, name=baked_name)[0]
    
    # 2. Create the Blend Shape
    bs_node = mc.blendShape(rigged_mesh, new_mesh)[0]
    
    # 3. FIX: Get the correct attribute name for the weight
    # We ask the node for its 'weight' list (alias list)
    weight_attributes = mc.listAttr(f"{bs_node}.w", multi=True)
    
    if weight_attributes:
        # Set the first target weight to 1
        mc.setAttr(f"{bs_node}.{weight_attributes[0]}", 1)
    
    print(f"Connected {rigged_mesh} to {new_mesh} via {bs_node}")
    
    # To be added after setAttr in your script:
    start = mc.playbackOptions(q=True, min=True)
    end = mc.playbackOptions(q=True, max=True)
    
    # Bake vertex animation (control points)
    mc.bakeResults(new_mesh, t=(start, end), simulation=True, controlPoints=True)
    
    # Delete the deformer - the mesh is now "Rig-Free"
    #cmds.delete(bs_node)
    
    print(f"Baked {rigged_mesh} to {new_mesh}")

    return new_mesh


def clone_and_assign_materials(target_mesh):
    # Get the shading groups connected to the baked mesh
    shapes = mc.listRelatives(target_mesh, shapes=True, fullPath=True)
    shading_groups = list(set(mc.listConnections(shapes, type='shadingEngine')))

    for sg in shading_groups:
        # 1. Find the actual shader (surfaceShader)
        shader = mc.listConnections(f"{sg}.surfaceShader")[0]
        
        # 2. Duplicate the shader network (the 'un' flag keeps connections to file nodes)
        new_shader = mc.duplicate(shader, upstreamNodes=True, name=f"local_{shader}")[0]
        
        # 3. Create a new local Shading Group
        new_sg = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=f"{new_shader}_SG")
        mc.connectAttr(f"{new_shader}.outColor", f"{new_sg}.surfaceShader", force=True)
        
        # 4. Assign the new local material to the baked mesh
        mc.sets(target_mesh, edit=True, forceElement=new_sg)
        
        print(f"Successfully localized material: {new_shader}")


def one_click_export(rigged_mesh):
    # Step 1: Bake it
    baked_mesh = bake_geo_clean(rigged_mesh)
    
    # Step 2: Fix the materials on the new baked mesh
    clone_and_assign_materials(baked_mesh)
    
    # Step 3: Clean up the temporary blendshape (if not already deleted)
    # mc.delete('temp_bake_BS') 
    
    print("Process Complete: Mesh is baked and materials are local.")


one_click_export(mc.ls(sl=True)[0])