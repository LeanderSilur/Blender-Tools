import bpy
import bmesh
import numpy as np
import mathutils
from math import floor, ceil

def get_mesh(name):
    if bpy.data.objects.get(name) == None:
        me = bpy.data.meshes.new(name)
        bpy.data.objects.new( name, me )
    return bpy.data.objects[name]

def write_smoke_to_bm(smoke_obj, bm):
    smoke_domain_mod = smoke_obj.modifiers[0]
    settings = smoke_domain_mod.domain_settings

    res = settings.resolution_max
    grid_density = np.array(settings.density_grid).reshape((res, res, res))
    grid_col = np.array(settings.color_grid).reshape((res, res, res, 4))
    grid_flame = np.array(settings.flame_grid).reshape((res, res, res))
    thres = np.max(grid_density)/4

    verts = np.array([smoke_obj.matrix_world @ v.co for v in smoke_obj.data.vertices])
    verts = verts.reshape((*verts.shape, 1))
    minmax = np.stack((np.min(verts, axis=0), np.max(verts, axis=0)))
    minmax = np.reshape(minmax, minmax.shape[:2])

    step = (minmax[1] - minmax[0]) / res

    density = bm.loops.layers.color.new("density")
    color = bm.loops.layers.color.new("color")
    flame = bm.loops.layers.color.new("flame")

    for z in range(0, grid_density.shape[0]):
        for y in range(0, grid_density.shape[1]):
            for x in range(0, grid_density.shape[2]):
                if grid_density[z, y, x] > thres:
                    mat = mathutils.Matrix.Translation((
                        minmax[0][0] + (x + 0.5) * step[0],
                        minmax[0][1] + (y + 0.5) * step[1],
                        minmax[0][2] + (z + 0.5) * step[2]
                    )).to_4x4()
                    mat = mat @ mathutils.Matrix.Diagonal(step * 0.95).to_4x4()
                        
                    verts = bmesh.ops.create_cube(bm, size=1, matrix=mat)['verts']
                    faces = set()
                    for v in verts:
                        for face in v.link_faces:
                            faces.add(face)
                    
                    for face in faces:
                        for loop in face.loops:
                            loop[density] = [grid_density[z, y, x]] * 4
                            loop[color] = grid_col[z, y, x]
                            loop[flame] = [grid_flame[z, y, x]] * 4

domain = bpy.data.objects['domain']
objects = bpy.data.collections['simulated'].objects
smoke = domain.modifiers[0]

depsgraph = bpy.context.evaluated_depsgraph_get()
smoke_obj = domain.evaluated_get(depsgraph)
smoke_domain_mod = smoke_obj.modifiers[0]
settings = smoke_domain_mod.domain_settings


for frame in range(settings.cache_frame_start, settings.cache_frame_end):
    print(frame)
    bpy.context.scene.frame_set(frame)
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    smoke_obj = domain.evaluated_get(depsgraph)
    
    bm = bmesh.new()
    
    write_smoke_to_bm(smoke_obj, bm)
    ob = get_mesh('simulated' + str(frame).zfill(2))
    try:
        objects.link(ob)
    except:
        pass # already in collection
    
    for i in (frame - 1, frame + 1):
        ob.hide_viewport = ob.hide_render = True
        ob.keyframe_insert('hide_viewport', frame=i)
        ob.keyframe_insert('hide_render', frame=i)
    ob.hide_viewport = ob.hide_render = False
    ob.keyframe_insert('hide_viewport', frame=frame)
    ob.keyframe_insert('hide_render', frame=frame)
        
    bm.to_mesh(ob.data)
    bm.free()

