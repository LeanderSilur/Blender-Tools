"""
Arun Leander, 2020
"""
import bpy
import subprocess
import json
from math import radians, degrees

def transferAnimation(action, take, bone):
    blendBoneName = bone.name
    boneName = blendBoneName
    for s, p in [['.l', 'Left'], ['.r', 'Right']]:
        if s in blendBoneName:
            boneName = p + blendBoneName.replace(s, "")
    
    if boneName in take:
        data_path = 'pose.bones["' + blendBoneName + '"].location'
        for i, name in enumerate(['tx', 'ty', 'tz']):
            takeCrv = take[boneName][name]
            if len(takeCrv):
                crv = action.fcurves.new(data_path, i)
                for frame in takeCrv:
                    crv.keyframe_points.insert(float(frame),
                        takeCrv[frame])
                        
        data_path = 'pose.bones["' + blendBoneName + '"].rotation_euler'
        for i, name in enumerate(['rx', 'ry', 'rz']):
            takeCrv = take[boneName][name]
            crv = action.fcurves.new(data_path, i)
            
            if len(takeCrv):
                for frame in takeCrv:
                    crv.keyframe_points.insert(float(frame),
                        radians(takeCrv[frame]))
            else:
                crv.keyframe_points.insert(0.0, 0.0)
        
        

filename = 'transfer.fbx'
namespace = 'dude:'

args = ['python33', bpy.path.abspath('//fbx/readFbxKeys.py'),  bpy.path.abspath('//fbx/' + filename), namespace]


print("________________")

p = subprocess.Popen(args, stdout=subprocess.PIPE)
out, err = p.communicate()


print("Convert Data")
takes = json.loads(out.decode('utf-8'))



print("Remove Actions")
for a in bpy.data.actions:
    if a.name != "T-Pose":
        bpy.data.actions.remove(a)


print("Import Actions\n\n")

keys = list(takes.keys()) 

for takeName in keys[:]:
    print(takeName)
    takeNameP = 'i' + takeName
    
    action = bpy.data.actions.get(takeNameP)
    if action == None:
        action = bpy.data.actions.new(takeNameP)
    action.use_fake_user = True
    
    for crv in action.fcurves:
        action.fcurves.remove(crv)
    
    for bone in bpy.context.object.pose.bones:
        transferAnimation(action, takes[takeName], bone)
    