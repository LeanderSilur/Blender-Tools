"""

Special Thanks to Andrew Yang for contributing the update to 2.8x!

"""

bl_info = {
    "name": "Curve Edit Tools",
    "author": "Arun Leander",
    "category": "Curve",
    "version": (0, 9),
    "blender": (2, 80, 0),
    "description": "In the edit mode of a bezier curve and press I to insert another bezier point.",
    "warning": "Read the preferences below.",
}

import bpy
import importlib

preferences = importlib.import_module('.preferences', package=__package__)
operators = importlib.import_module('.operators', package=__package__)

addon_keymaps = []

def add_keymap():
    wm = bpy.context.window_manager

    km = wm.keyconfigs.addon.keymaps.new(name='Curve', space_type='EMPTY')
    kmi = km.keymap_items.new(operators.InsertBezierPoint.bl_idname, 'I', 'PRESS')

    addon_keymaps.append((km, kmi))

def remove_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register():
    bpy.utils.register_class(operators.InsertBezierPoint)
    bpy.utils.register_class(preferences.CURVE_OT_insert_bezier_spline_points)
    
    add_keymap()
    

def unregister():
    remove_keymap()
    
    bpy.utils.unregister_class(preferences.CURVE_OT_insert_bezier_spline_points)
    bpy.utils.unregister_class(operators.InsertBezierPoint)
