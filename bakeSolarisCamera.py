import hou

def bake_solaris_camera():
    selected = hou.selectedNodes()
    if not selected or selected[0].type().category() != hou.lopNodeTypeCategory():
        hou.ui.displayMessage("Erreur : Sélectionnez un nœud LOP.", severity=hou.severityType.Error)
        return
        
    lop_node = selected[0]
    stage = lop_node.stage()
    if not stage:
        return

    cam_paths = [prim.GetPath().pathString for prim in stage.Traverse() if prim.GetTypeName() == "Camera"]
    if not cam_paths:
        return

    if len(cam_paths) == 1:
        cam_path = cam_paths[0]
    else:
        choices = hou.ui.selectFromList(cam_paths, message="Sélectionnez la caméra :", exclusive=True)
        if not choices: return
        cam_path = cam_paths[choices[0]]

    start_frame, end_frame = hou.playbar.playbackRange()
    obj_net = hou.node('/obj')
    cam_name = cam_path.split('/')[-1] + "_baked"
    
    with hou.undos.group("Bake LOP Camera"):
        fetch_cam = obj_net.createNode('lopimportcam', 'TEMP_fetch_' + cam_name)
        fetch_cam.parm('loppath').set(lop_node.path())
        
        if fetch_cam.parm('camerapath'):
            fetch_cam.parm('camerapath').set(cam_path)
        elif fetch_cam.parm('primpath'):
            fetch_cam.parm('primpath').set(cam_path)

        baked_cam = obj_net.createNode('cam', cam_name)
        
        parms_lens = ['focal', 'aperture', 'near', 'far']

        for frame in range(int(start_frame), int(end_frame) + 1):
            # La matrice requiert le temps en secondes, pas en frames
            time = hou.frameToTime(frame)
            
            # 1. Extraction de la matrice globale et décomposition
            mat = fetch_cam.worldTransformAtTime(time)
            translates = mat.extractTranslates()
            rotates = mat.extractRotates()
            
            # Écriture des clés de Translation
            for i, axis in enumerate(['tx', 'ty', 'tz']):
                key = hou.Keyframe()
                key.setFrame(frame)
                key.setValue(translates[i])
                baked_cam.parm(axis).setKeyframe(key)
                
            # Écriture des clés de Rotation
            for i, axis in enumerate(['rx', 'ry', 'rz']):
                key = hou.Keyframe()
                key.setFrame(frame)
                key.setValue(rotates[i])
                baked_cam.parm(axis).setKeyframe(key)

            # 2. Écriture des paramètres optiques (eux sont bien sur les parms)
            for parm_name in parms_lens:
                fetch_parm = fetch_cam.parm(parm_name)
                if fetch_parm:
                    val = fetch_parm.evalAtTime(time)
                    key = hou.Keyframe()
                    key.setFrame(frame)
                    key.setValue(val)
                    baked_cam.parm(parm_name).setKeyframe(key)

        fetch_cam.destroy()
        baked_cam.setSelected(True, clear_all_selected=True)
        hou.ui.displayMessage(f"Caméra générée : {baked_cam.path()}")

bake_solaris_camera()