import hou

#Selection of the image files
file_paths = hou.ui.selectFile(
    title="Select Images",
    file_type=hou.fileType.Image,
    multiple_select=True
)

if file_paths:
    # Clean up the paths
    images = [f.strip() for f in file_paths.split(";") if f.strip()]
    stage = hou.node("/stage")
    
    # Create the Material Library and the Assign Material node
    mat_lib = stage.createNode("materiallibrary", "auto_material_library")
    assign_mat = stage.createNode("assignmaterial", "auto_assign_material")
    assign_mat.setInput(0, mat_lib)

    # Prepare the number of assignments
    if assign_mat.parm("nummaterials"):
        assign_mat.parm("nummaterials").set(len(images))

    # Main loop
    for i, path in enumerate(images, start=0):
        
        material_name = f"mat_image_{i}"
        
        # Create the subnet
        material = mat_lib.createNode("subnet", material_name)
        
        # ---- SET THE OUTPUT / MATERIAL FLAG ----
        material.setGenericFlag(hou.nodeFlag.Material, True)
        
        # ---- CREATE MATERIALX NODES ----
        subnetConnectorSurface = material.createNode("subnetconnector", "surface_output")
        subnetConnectorSurface.parm("connectorkind").set(1)
        subnetConnectorSurface.parm("parmname").set("surface")
        subnetConnectorSurface.parm("parmlabel").set("Surface")
        subnetConnectorSurface.parm("parmtype").set(24)

        subnetConnectorDisplacement = material.createNode("subnetconnector", "displacement_output")
        subnetConnectorDisplacement.parm("connectorkind").set(1)
        subnetConnectorDisplacement.parm("parmname").set("displacement")
        subnetConnectorDisplacement.parm("parmlabel").set("Displacement")
        subnetConnectorDisplacement.parm("parmtype").set(25)

        surface = material.createNode("mtlxstandard_surface", "mtlxstandard_surface")
        albedoImage = material.createNode("mtlximage", "Albedo")
        
        separate_alpha = material.createNode("mtlxseparate4c", "separate_alpha")

        # ---- CONNECTIONS ----
        subnetConnectorSurface.setNamedInput("suboutput", surface, "out")
        surface.setNamedInput("base_color", albedoImage, "out")
        
        # ---> NEW: Connect Albedo to Separate, and Separate 'outa' to Surface 'opacity'
        separate_alpha.setNamedInput("in", albedoImage, "out")
        surface.setNamedInput("opacity", separate_alpha, "outa")
        
        # ---- PARAMETER CONFIGURATION ----
        albedoImage.parm("file").set(path)
        albedoImage.parm("signature").set("color4")

        material.layoutChildren()

        # ---- USD ASSIGNMENT ----
        usd_path = f"/materials/{material.name()}"
        target_group = f"**/groupe_{i}"
        
        parm_idx = i + 1
        
        if assign_mat.parm(f"primpattern{parm_idx}"):
            assign_mat.parm(f"primpattern{parm_idx}").set(target_group)
        elif assign_mat.parm(f"primitives{parm_idx}"):
            assign_mat.parm(f"primitives{parm_idx}").set(target_group)
            
        if assign_mat.parm(f"matspecpath{parm_idx}"):
            assign_mat.parm(f"matspecpath{parm_idx}").set(usd_path)
        elif assign_mat.parm(f"materialpath{parm_idx}"):
            assign_mat.parm(f"materialpath{parm_idx}").set(usd_path)

    # Final cleanup and layout
    mat_lib.layoutChildren()
    assign_mat.moveToGoodPosition()
    
    # Success message
    hou.ui.displayMessage(f"Awesome! {len(images)} materials were successfully generated")