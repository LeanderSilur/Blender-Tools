"""
Arun Leander, 2017


Derivate of blender.stackexchange.com answer https://blender.stackexchange.com/a/108233/30849
by user "batFinger" https://blender.stackexchange.com/users/15543

"""

import bpy
import re

context = bpy.context
ob = context.object
# get the mirrored name
def get_mirror(g):
    return ob.vertex_groups.get(re.sub(r'(.*)L', r'\1R', g.name))

mirror_groups = [(vg, get_mirror(vg)) for vg in ob.vertex_groups
        if vg.name.endswith(".L")]
mirror_groups = [m for m in mirror_groups if not (m[0].lock_weight or m[1].lock_weight)]

single_groups = [vg for vg in ob.vertex_groups if not vg.lock_weight and vg.name[-2:-1] is not "."]
print("Mirroring")
for lg, rg in mirror_groups:
    if rg is None:
        print(lg.name, "has no mirror group")
        continue
    print("    ", lg.name, ">", rg.name)

    lverts = [v for v in ob.data.vertices 
            if lg.index in [vg.group for vg in v.groups]]  
    rverts = [v for v in ob.data.vertices]

    for lv in lverts:
        vec = lv.co.copy()
        vec.x *= -1
        # sort rverts by distance from lvert
        rverts.sort(key=lambda v: (vec - v.co).length) 
        # pop and set the rvert
        rv = rverts.pop(0)
        rv.co = vec 
        rg.add([rv.index], lg.weight(lv.index), 'REPLACE')

for g in single_groups:
    print("    ", g.name)

    lverts = [v for v in ob.data.vertices if v.co.x > 0]
    rverts = [v for v in ob.data.vertices if v.co.x < 0]
    print(len(lverts))
    print(len(rverts))
    for lv in lverts:
        vec = lv.co.copy()
        vec.x *= -1
        # sort rverts by distance from lvert
        rverts.sort(key=lambda v: (vec - v.co).length) 
        # pop and set the rvert
        rv = rverts.pop(0)
        rv.co = vec 
        g.add([rv.index], g.weight(lv.index), 'REPLACE')