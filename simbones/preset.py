from bpy.types import Operator
from bl_operators.presets import AddPresetBase
import bpy

class AddPresetSimbone(AddPresetBase, Operator):
    bl_idname = 'pose.simbone_bone_preset_add'
    bl_label = 'Add a preset'
    preset_menu = 'SIMBONE_PT_bone_presets'

    preset_defines = ['bone = bpy.context.active_pose_bone.simbone']
    preset_values = [
        'bone.active',
        'bone.c_a',
        'bone.c_d',
        'bone.custom_force',
        'bone.m',
        'bone.up_offset',
    ]
    preset_subdir = 'simbone/bone'


class AddPresetSimboneWorld(AddPresetBase, Operator):
    bl_idname = 'pose.simbone_world_preset_add'
    bl_label = 'Add a preset'
    preset_menu = 'SIMBONE_PT_world_presets'

    preset_defines = ['world = bpy.context.scene.simboneworld']
    preset_values = [
        'world.active',
        'world.gravity',
        'world.precision',
        'world.spaceScale',
        'world.timeScale',
        'world.use_scene_gravity',
        'world.wind',
    ]
    preset_subdir = 'simbone/world'



classes = (
    AddPresetSimbone,
    AddPresetSimboneWorld,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)



def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)