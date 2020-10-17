"""
Panels and Properties are defined here.

The Simulation Panel is located in
    Properties Area > Bone Properties > Simulation

Global properties are located in
    Properties Area > Scene Properties > Bone World

"""

import bpy
from bl_ui.utils import PresetPanel
import math
import mathutils
import decimal

class SimBone(bpy.types.PropertyGroup):
    active: bpy.props.BoolProperty(default=False)
    
    # rest θ, φ, strength
    m: bpy.props.FloatProperty(default=1,
        name='Mass',
        unit='MASS',
        description='Mass of the bob in the pendulum simulation.')
    custom_force: bpy.props.FloatVectorProperty(
        name='Custom Force',
        soft_min=-10, soft_max=10,
        description='Custom Force. Can resist gravity.',
        subtype='ACCELERATION', unit='ACCELERATION')
    up_offset: bpy.props.FloatProperty(default=90,
        name='Up Offset', description='Up axis in spherical coordinates.',
        subtype ='ANGLE', unit='ROTATION',
        min=0, max=math.pi)
    
    c_a: bpy.props.FloatProperty(default=0, name='Friction')
    c_d: bpy.props.FloatProperty(default=0, name='Drag')


class SimBoneWorld(bpy.types.PropertyGroup):
    active: bpy.props.BoolProperty(default=False)
    
    use_scene_gravity: bpy.props.BoolProperty(default=True,
        name = 'Use Scene Gravity',
        description='Use a the gravity value specified in the scene\'s gravity panel.')
    gravity: bpy.props.FloatVectorProperty(size=3, default=(0, 0, -10),
        name='Gravity',
        description='Gravity',
        subtype='ACCELERATION',
        unit='ACCELERATION',
    )
    wind: bpy.props.FloatVectorProperty(size=3, default=(0, 0, 0),
        name='Wind',
        description='Wind velocity.',
        subtype='VELOCITY')

    timeScale: bpy.props.FloatProperty(default=1,
        name='Speed',
        description='Scale time. Higher speed values, the simulation will play back faster.',
        min=0.01,
        unit='TIME')
    spaceScale: bpy.props.FloatProperty(default=1,
        name='Scale',
        description='Scale of the simulation. Higher values enlargen the scene.',
        min=0.01,
        unit='LENGTH')
    precision: bpy.props.FloatProperty(default=1,
        name='Precision',
        description='Precision used by the scipy solver.',
        min=0.01)


class SIMBONE_PT_bone_presets(PresetPanel, bpy.types.Panel):
    bl_label = 'Simbone Bone Presets'
    preset_subdir = 'simbone/bone'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'pose.simbone_bone_preset_add'

class BONE_PT_simbone(bpy.types.Panel):
    """Panel in the Properties Area"""
    bl_label = "Simulation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header_preset(self, _context):
        SIMBONE_PT_bone_presets.draw_panel_header(self.layout)

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.active_pose_bone != None

    def draw_header(self, context):
        bone = context.active_pose_bone
        self.layout.prop(bone.simbone, "active", text="")

    def draw(self, context):
        bone = context.active_pose_bone
        if bone == None: return None
        simbone = bone.simbone

        layout = self.layout
        layout.use_property_split = True
        layout.active = simbone.active

        layout.row().prop(simbone, "m")

        col = layout.column(align=True)
        col.prop(simbone, "custom_force", slider=1)
        col.prop(simbone, "up_offset", slider=1)
        
        col = layout.column(align=True)
        col.prop(simbone, "c_a")
        col.prop(simbone, "c_d")

class SIMBONE_PT_world_presets(PresetPanel, bpy.types.Panel):
    bl_label = 'Simbone Scene Presets'
    preset_subdir = 'simbone/world'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'pose.simbone_world_preset_add'
    

class SCENE_PT_simboneworld(bpy.types.Panel):
    """Panel in the Properties Area"""
    bl_label = "Bone Simulation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header_preset(self, _context):
        SIMBONE_PT_world_presets.draw_panel_header(self.layout)

    def draw_header(self, context):
        self.layout.prop(context.scene.simboneworld, "active", text="")

    def draw(self, context):
        simboneworld = context.scene.simboneworld
        layout = self.layout
        layout.active = simboneworld.active
        layout.use_property_split = True

        layout.row().prop(simboneworld, "use_scene_gravity")
                
        if simboneworld.use_scene_gravity and not context.scene.use_gravity:
            layout.row().label(text="Disabling scene gravity doesn't change anything.", icon='QUESTION')
        if not simboneworld.use_scene_gravity:
            layout.row().prop(simboneworld, "gravity")

        layout.row().prop(simboneworld, "wind")
        layout.row().prop(simboneworld, "timeScale")
        layout.row().prop(simboneworld, "spaceScale")
        layout.row().prop(simboneworld, "precision")

class VIEW3D_MT_simbone(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_simbone"
    bl_label = "Simbones"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.simbones_bake")
        layout.separator()
        layout.label(text="Custom Force")
        layout.operator("pose.simbones_translate_custom_force", text="Move")
        layout.operator("pose.simbones_align_custom_force", text="Auto Align")
        layout.operator("pose.simbones_scale_custom_force", text="Auto Scale")

def add_simbone_menu(self, context):
    if context.mode == 'POSE':
        self.layout.menu(VIEW3D_MT_simbone.bl_idname)


classes = (
    SimBone,
    SimBoneWorld,
    SIMBONE_PT_bone_presets,
    BONE_PT_simbone,
    SIMBONE_PT_world_presets,
    SCENE_PT_simboneworld,
    VIEW3D_MT_simbone,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.PoseBone.simbone = bpy.props.PointerProperty(type=SimBone)
    bpy.types.Scene.simboneworld = bpy.props.PointerProperty(type=SimBoneWorld)

    bpy.types.VIEW3D_MT_editor_menus.append(add_simbone_menu)


def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(add_simbone_menu)
    
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)