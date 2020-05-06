"""
Arun Leander, 2018
"""


import mathutils
import math
import numpy as np
import bpy

def get_T(t):
    return [[1, 3, 3, 1][i] * math.pow(1-t, 3-i) * math.pow(t, i) for i in range(4)]


rig = bpy.context.object
bones = [rig.pose.bones[rig.data.bones.active.name]]

for i in range(3):
    bones.append(bones[-1].children[0])
    
coords = [tuple(bone.matrix.decompose()[0]) for bone in bones]
print(coords)

p = np.array(coords)

# 1st equation
tc = get_T(1/3)
lhs1 = p[1] - (p[0] * tc[0] + p[3] * tc[3])
tc1 = tc

# 2nd equation
tc = get_T(2/3)
lhs2 = p[2] - (p[0] * tc[0] + p[3] * tc[3])
tc2 = tc

b = np.array([lhs1, lhs2])

a = np.array([[tc1[1], tc1[2]], [tc2[1], tc2[2]]])

x = np.linalg.solve(a, b)

print(x)
print(np.allclose(np.dot(a, x), b))

bpy.data.objects['a'].location = mathutils.Vector(tuple(x[0]))
bpy.data.objects['b'].location = mathutils.Vector(tuple(x[1]))