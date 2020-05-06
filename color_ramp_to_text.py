import bpy
import math

ob = bpy.context.object

data = {}

for slot in ob.material_slots:
    nodes = slot.material.node_tree.nodes
    name = slot.material.name
    data[name] = []
    
    ramp = nodes.get("ColorRamp").color_ramp
    # snapping
    #for el in ramp.elements:
    #    el.position = el.position - el.position % (1/16)
    # extract data
    for i in range(16):
        v = ramp.evaluate(i / 16)
        v = [round(i, 6) for i in v]
        data[name].append(v)
        
    
    
result = ""
for key in data:
    result += "public static readonly Color[] " + key + " = new Color[]\n{"
    for col in data[key]:
        result += "\nnew Color("
        for v in col:
            result += str(v) + "f, "
        result = result[:-2] + "),"
    result = result[:-1] + "\n};\n"
    
colors = bpy.data.texts.get("colors")
if colors == None:
    colors = bpy.data.texts.new("colors")
colors.from_string(result)