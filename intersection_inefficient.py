"""
Arun Leander, 2018
"""
import bpy
import bmesh
import math
from mathutils.bvhtree import BVHTree
import mathutils

scene = bpy.context.scene

def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=True):
    """
    Returns a transformed, triangulated copy of the mesh
    """

    assert(obj.type == 'MESH')

    if apply_modifiers and obj.modifiers:
        me = obj.to_mesh(bpy.context.scene, True, 'PREVIEW', calc_tessface=False)
        bm = bmesh.new()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    else:
        me = obj.data
        if obj.mode == 'EDIT':
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

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm

def closest_point_to_line(v, w, p):
    l2 = length_squared(w-v)
    
    if (l2 == 0.0):
        return v
    
    t = ((p-v).dot(w-v))/l2
    return v + w * t

def get_intersections_tris(face, p0, p1):
    p0 = p0.co
    p1 = p1.co
    d = (p1 - p0)
    
    n = face.normal
    nd = n.dot(face.verts[0].co)
    
    denom = d.dot(n)
    if denom == 0:
        print("parralel")
        return None
    t = (nd - p0.dot(n))/denom

    if (t < 0 or t > 1):
        return None
    
    p = p0 + t * d
    
    longest_edge = face.edges[0]
    for e in face.edges[1:]:
        if e.calc_length() > longest_edge.calc_length():
            longest_edge = e
            
    v1, v2 = [v.co for v in longest_edge.verts]
    v3 = [v for v in face.verts if v not in longest_edge.verts][0].co
    
    eu = (v2 - v1)
    eu.normalize()
    
    ev = (v3 - v1) - eu * (eu.dot(v3-v1))
    ev.normalize()
    
    w = (v2-v1).length
    g = eu.dot(v3 - v1)
    h = ev.dot(v3 - v1)
    
    #v1 = (0, 0)
    #v2 = (w, 0)
    #v3 = (g, h)
    
    u = eu.dot(p-v1)
    v = ev.dot(p-v1)
    
    if u < 0 or v < 0:
        return None
    if u > w or v > h:
        return None
    if u <= g and v > u*h/g:
        return None
    if u >= g and v > (w-u)*h/(w-g):
        return None

    return p
    
def get_intersections_faces(face1, face2):
    locs = []
    for edges, face in [[face1.edges, face2], [face2.edges, face1]]:
        for edge in edges:
            ret = get_intersections_tris(face, *edge.verts)
            if ret is not None:
                locs.append(ret)
    return locs

def create_mesh_obj(bm, p_name = "intersection_mesh"):
    if (p_name not in bpy.data.meshes):
        me_tmp = bpy.data.meshes.new(name = p_name)
    me = bpy.data.meshes[p_name]
    bm.to_mesh(me)
    
    if (p_name not in bpy.data.objects):
        ob = bpy.data.objects.new(name = p_name, object_data = me)
        scene.objects.link(ob)
    else:
        ob = bpy.data.objects[p_name]
        ob.data = me
    scene.update()
    return ob


def intersection_from_bm(bm):
    bvh = BVHTree.FromBMesh(bm, epsilon = 0.00001)
    
    bm_out = bmesh.new()
    
    faces = bm.faces
    for face1 in faces:
        for face2 in faces:
            if face1.index != face2.index:
                # edges of one against the others
                locs = get_intersections_faces(face1, face2)
                print(len(locs))
                for loc in locs:
                    bm_out.verts.new(loc)
                    
                if len(locs) == 2:
                    bm_out.edges.new(bm_out.verts[-2:])
                
                return bm_out
    
    return bm_out

def extrude_towards(bm, obj, amount = 0):
    
    ret = bmesh.ops.extrude_edge_only(bm, edges = bm.edges[:], use_select_history = False)
    ex = ret["geom"]
    i = 0
    while (i < len(ex)):
        if (not isinstance(ex[i], bmesh.types.BMVert)):
            del ex[i]
        else:
            i += 1
            
    del ret
    
    mat = mathutils.Matrix.Translation(obj.location).inverted()
    bmesh.ops.scale(bm, vec = (amount, amount, amount), space = mat, verts = ex)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True

ob = bpy.data.objects['Cube']
bm_orig = bmesh_copy_from_object(ob)
bm_result = intersection_from_bm(bm_orig)
create_mesh_obj(bm_result)



camera = bpy.context.scene.camera

#print(locs)