import bpy

ob = bpy.context.scene.objects.active

for b in ob.data.bones:
    if b.name[:4] == "Left":
        b.name = b.name[4:] + ".l"
    elif b.name[:5] == "Right":
        b.name = b.name[5:] + ".r"
    elif b.name[-2:] == ".l":
        b.name = "Left" + b.name[:-2]
    elif b.name[-2:] == ".r":
        b.name = "Right" + b.name[:-2]


