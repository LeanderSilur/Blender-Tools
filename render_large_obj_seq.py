"""
Arun Leander, 2018
"""
import bpy
import os

directory = "my_directory"
files = os.listdir(directory)


for o in bpy.data.objects:
    o.select = False


for i in range(3, 51):
    path = os.path.join(directory, str(i) + ".obj")
    
    bpy.ops.import_scene.obj(filepath=path)
    bpy.ops.object.shade_smooth()
    
    bpy.context.scene.render.filepath = "//images/" + str(i).zfill(4) + ".png"
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.delete()

    
    print("imported", i)


print(files)