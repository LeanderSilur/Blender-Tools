import bpy
import math

def handler(scene):
    # get an area of type VIEW_3D
    areas = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D']
    if not len(areas):
        return
    
    region3d = areas[0].spaces[0].region_3d
    
    # get the view matrix
    view_mat_inv = region3d.view_matrix
    
    # setup two test objects
    # 'Cube' contains some vertices
    # object 'A' will snap to the vertex closest the the view matrix
    ob = bpy.data.objects['Cube']
    em = bpy.data.objects['A']
    
    if region3d.is_perspective:
        vertices = [[v, (view_mat_inv*v.co).length] for v in ob.data.vertices]
    else:
        vertices = [[v, -(view_mat_inv*v.co).z] for v in ob.data.vertices]
        
    # use a lamda expression to get closest
    em.location = min(vertices, key = lambda x: x[1])[0].co

for h in bpy.app.handlers.scene_update_pre:
    bpy.app.handlers.scene_update_pre.remove(h)

bpy.app.handlers.scene_update_pre.append(handler)
