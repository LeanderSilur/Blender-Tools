bl_info = {
    "name": "Simbones",
    "author": "Arun Leander",
    "version": (1, 0, 0),
    "blender": (2, 82, 0),
    "location": "View3D",
    "description": "Bone Pendulum Simulation Tools",
    "category": "Rigging",
    "support": "TESTING",
}
import bpy

import importlib
gui = importlib.import_module('.gui', package=__package__)
operators = importlib.import_module('.operators', package=__package__)

addon_keymaps = []

def add_keymap():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Pose', space_type='EMPTY')
    kmi = km.keymap_items.new('wm.call_menu', 'B', 'PRESS', ctrl=True)
    kmi.properties.name = gui.POSE_MT_simbone.bl_idname

    addon_keymaps.append((km, kmi))

def remove_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

def register():
    # Types
    bpy.utils.register_class(gui.SimBone)
    bpy.utils.register_class(gui.SimBoneWorld)
    bpy.types.PoseBone.simbone = bpy.props.PointerProperty(type=gui.SimBone)
    bpy.types.Scene.simboneworld = bpy.props.PointerProperty(type=gui.SimBoneWorld)
    # Operators
    bpy.utils.register_class(operators.TranslateCustomForce)
    bpy.utils.register_class(operators.BakeBoneSimulation)
    bpy.utils.register_class(operators.AlignCustomForce)
    bpy.utils.register_class(operators.ScaleCustomForce)
    # UI
    bpy.utils.register_class(gui.BONE_PT_simbone)
    bpy.utils.register_class(gui.SCENE_PT_simboneworld)
    bpy.utils.register_class(gui.POSE_MT_simbone)

    bpy.types.VIEW3D_MT_editor_menus.append(gui.add_simbone_menu)
    
    add_keymap()
    
 
def unregister():
    remove_keymap()

    bpy.types.VIEW3D_MT_editor_menus.remove(gui.add_simbone_menu)

    bpy.utils.unregister_class(gui.POSE_MT_simbone)
    
    bpy.utils.unregister_class(gui.SCENE_PT_simboneworld)
    bpy.utils.unregister_class(gui.BONE_PT_simbone)
    bpy.utils.unregister_class(gui.SimBoneWorld)
    bpy.utils.unregister_class(gui.SimBone)

    bpy.utils.unregister_class(operators.BakeBoneSimulation)
    bpy.utils.unregister_class(operators.TranslateCustomForce)
    bpy.utils.unregister_class(operators.AlignCustomForce)
    bpy.utils.unregister_class(operators.ScaleCustomForce)