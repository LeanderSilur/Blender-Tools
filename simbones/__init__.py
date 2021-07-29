bl_info = {
    "name": "Simbones",
    "author": "Arun Leander",
    "version": (1, 0, 1),
    "blender": (2, 82, 0),
    "location": "View3D",
    "description": "Bone Pendulum Simulation Tools",
    "category": "Rigging",
    "support": "TESTING",
}
import bpy

addon_keymaps = []

def add_keymap():
    from . import gui
    
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Pose', space_type='EMPTY')
    kmi = km.keymap_items.new('pose.simbones_bake', 'B', 'PRESS', ctrl=True)
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new('pose.simbones_translate_custom_force', 'F', 'PRESS')
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new('pose.simbones_align_custom_force', 'F', 'PRESS', ctrl=True, shift=True)
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new('pose.simbones_scale_custom_force', 'G', 'PRESS', ctrl=True, shift=True)
    addon_keymaps.append((km, kmi))


def remove_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

def install_scipy():
    try:
        import scipy
    except Exception as e:
        print("Installing Scipy...")
        import sys
        import ensurepip
        import subprocess
        ensurepip.bootstrap()
        subprocess.call([sys.executable, "-m", "pip", "install", "scipy"])

def register():
    install_scipy()

    from . import gui
    from . import operators
    from . import preset

    gui.register()
    operators.register()
    preset.register()
    
    add_keymap()

def unregister():
    remove_keymap()

    from . import gui
    from . import operators
    from . import preset

    gui.unregister()
    operators.unregister()
    preset.unregister()