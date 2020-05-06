"""
Arun Leander, 2018

"""

import bpy
import bmesh
import mathutils

def get_bone_name(data_path):
    prefix = 'pose.bones'
    if data_path[:len(prefix)] != prefix:
        raise Exception('Prefix does not match pose bone scheme: ' + data_path)
    bone_name = data_path[len(prefix):].split('[')[1].split(']')[0][1:-1]
    return bone_name

def mirror_bone_name(name):
    if name[-2:] == '.l':
        return name[:-2] + '.r'
    return name

def mirror_dp(data_path):
    try:
        bone_name = get_bone_name(data_path)
    except:
        bone_name = '###'
    data_path_mirror = data_path.replace(bone_name, mirror_bone_name(bone_name))
    return data_path_mirror

#con = bpy.context.object.pose.bones[3].constraints[0]
def copy_driver_attr(orig, copy):
    # a to b
    copy.type = orig.type
    for var_orig in orig.variables:
        var = copy.variables.new()
        
        var.name = var_orig.name
        var.type = var_orig.type
        
        for t, t_orig in zip(var.targets, var_orig.targets):
            t.id = t_orig.id
            t.bone_target = mirror_bone_name(t_orig.bone_target)
            t.transform_space = t_orig.transform_space
            t.transform_type = t_orig.transform_type
            if var.type == 'SINGLE_PROP':
                t.id_type   = t_orig.id_type
                t.data_path = mirror_dp(t_orig.data_path)
    copy.show_debug_info = orig.show_debug_info
    copy.expression = orig.expression
    copy.use_self = orig.use_self

def remove_driver(rig, data_path):
    for driver in rig.animation_data.drivers:
        if driver.data_path == data_path:
            rig.driver_remove(data_path)

def mirror_drivers(rig):
    if rig.animation_data == None:
        print('No drivers or fcurves.')
        return
    drivers = rig.animation_data.drivers
    
    copied_drivers = []
    for driver in drivers:
        dp = driver.data_path
        bone_name = get_bone_name(dp)
        
        
        dp_mirrored = mirror_dp(dp)
        if dp != dp_mirrored:
            if rig.pose.bones[bone_name].bone.select:
                if dp in copied_drivers:
                    print('Skipping ' + dp
                        + ' because it was already handled.')
                else:
                    dr_orig = driver.driver
                    remove_driver(rig, dp_mirrored)
                    created_graphs = rig.driver_add(dp_mirrored)
                    if isinstance(created_graphs, list):
                        orig_graphs  = [d for d in drivers if d.data_path == dp]
                        
                        for orig, copy in zip(orig_graphs, created_graphs):
                            copy_driver_attr(orig.driver, copy.driver)
                        
                    else:
                        dr_copy = created_graphs.driver
                        copy_driver_attr(dr_orig, dr_copy)
                copied_drivers.append(dp)
        else:
            print("not left driver found:", driver.data_path[:24], '...')

def mirror_constraints(rig):
    # copy constraints from selected to mirrored bones
    pose_bones = rig.pose.bones

    for bone in pose_bones:
        mirrored_name = mirror_bone_name(bone.name)
        if bone.bone.select and bone.name != mirrored_name:
            mirror_bone = pose_bones.get(mirrored_name)
            if mirror_bone == None:
                raise Exception("Missing a mirrored bone: " + mirrored_name + ".")
            
            for constraint in mirror_bone.constraints:
                mirror_bone.constraints.remove(constraint)
                
            for constraint in bone.constraints:
                mirron_con = mirror_bone.constraints.new(constraint.type.upper())
                for attr in dir(constraint):
                    if attr[:1] != '_':
                        value = getattr(constraint, attr)
                        if attr == 'subtarget' or attr == 'pole_subtarget':
                            value = mirror_bone_name(value)
                        try:
                            setattr(mirron_con, attr, value)
                        except:
                            print('Failed to set constraint ' + attr + ' on bone ' + mirrored_name)


def create_mesh(bm, p_name = "my_mesh"):
    if (p_name not in bpy.data.meshes):
        me_tmp = bpy.data.meshes.new(name = p_name)
    me = bpy.data.meshes[p_name]
    bm.to_mesh(me)
    
    if (p_name not in bpy.data.objects):
        ob = bpy.data.objects.new(name = p_name, object_data = me)
        bpy.context.scene.objects.link(ob)
    else:
        ob = bpy.data.objects[p_name]
        ob.data = me
    bpy.context.scene.update()
    return ob
def get_bm(ob):
    if ob.modifiers:
        me = ob.to_mesh(bpy.context.scene, True, 'PREVIEW', calc_tessface=False)
        bm = bmesh.new()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    else:
        me = ob.data
        if ob.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    # Remove custom data layers to save memory
    for elem in (bm.faces, bm.edges, bm.verts, bm.loops):
        for layers_name in dir(elem.layers):
            if not layers_name.startswith("_"):
                layers = getattr(elem.layers, layers_name)
                for layer_name, layer in layers.items():
                    layers.remove(layer)
    return bm

def mirror_bone_settings(rig):
    pose_bones = rig.pose.bones
    for bone in pose_bones:
        mirrored_name = mirror_bone_name(bone.name)
        if bone.bone.select and bone.name != mirrored_name:
            mirror_bone = pose_bones.get(mirrored_name)
            #custom shapes
            mirror_bone.rotation_mode = bone.rotation_mode
            mirror_bone.bone.hide = bone.bone.hide
            mirror_bone.bone.show_wire = bone.bone.show_wire
            mirror_bone.use_custom_shape_bone_size = bone.use_custom_shape_bone_size
            mirror_bone.custom_shape_scale = bone.custom_shape_scale
            
            if bone.custom_shape != None:
                ob = bone.custom_shape
                if ob.name != mirror_bone_name(ob.name):
                    bm = get_bm(bone.custom_shape)
                    mat_sca = mathutils.Matrix.Scale(-1, 4, (1.0, 0.0, 0.0))
                    bm.transform(mat_sca)
                    ob = create_mesh(bm, mirror_bone_name(ob.name))
                    bm.free()
                mirror_bone.custom_shape = ob
                
                shape_transform = bone.custom_shape_transform
                if shape_transform != None:
                    mirror_name = mirror_bone_name(shape_transform.name)
                    shape_transform = rig.pose.bones[mirror_name]
                mirror_bone.custom_shape_transform = shape_transform
            
    pass

def mirror_active_rig():
    rig = bpy.context.object
    if rig.type != 'ARMATURE':
        print('Not armature.')
        return
    
    mirror_constraints(rig)
    mirror_drivers(rig)
    mirror_bone_settings(rig)
    
mirror_active_rig()