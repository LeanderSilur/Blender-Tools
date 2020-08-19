import bpy

def modify_strip_keyframes(scene_name, strip_name, keyframe_values = [1.0, 0.0]):
    
    scene = bpy.data.scenes.get(scene_name)
    if scene == None:
        print("Scene not found.")
        return
    
    if (scene.animation_data == None or scene.sequence_editor == None):
        print("No strips with keyframes.")
        return
    
    strip = scene.sequence_editor.sequences.get(strip_name)
    if strip == None:
        print("Strip not found.")
        return
    
    data_path = strip.path_from_id("blend_alpha")
    fcrv = scene.animation_data.action.fcurves.find(data_path)
    
    if fcrv == None:
        print("Strip not found.")
        return
    
    if len(fcrv.keyframe_points) != len(keyframe_values):
        print("The strip has " + str(len(fcrv.keyframe_points)) +
            " keys, but " + str(len(keyframe_values)) + " values were supplied.")
        return
    
    # If we reached this point, we have a blend_alpha fcurve with as many keys
    # as the keyframe_values parameter.
    
    for i in range(len(fcrv.keyframe_points)):
        key = fcrv.keyframe_points[i]
        key.co.y = keyframe_values[i]
        key.handle_left.y = keyframe_values[i]
        key.handle_right.y = keyframe_values[i]
        key.handle_left.x = key.co.x
        key.handle_right.x = key.co.x
    
modify_strip_keyframes("Scene", "cat", keyframe_values = [1, 0.5])
bpy.ops.sequencer.refresh_all()
