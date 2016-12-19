# 
# http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Guidelines/Addons/metainfo
#
bl_info = {
    "name": "Le Animation Tools",
    "description": "Blender Animation Tools Panel combining useful functions, scattered across the UI.",
    "author": "Arun Leander",
    "version": (0, 0),
    "blender": (2, 78, 0),
    "location": "3D View > Properties Panel",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "Animation"}

import bpy

class le_animation_tools_ui(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Animation Tools"
    bl_idname = "OBJECT_PT_le_animation_tools_ui"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        row = layout.row()
        row.prop(context.tool_settings, "use_keyframe_insert_auto", text="")
        row.prop(context.tool_settings, "keyframe_type", text="")
        row.operator("anim.keyframe_insert", text="", icon="KEY_HLT")
        row.operator("anim.keyframe_delete", text="", icon="KEY_DEHLT")
        row = layout.row()
        row.prop(context.user_preferences.edit, "keyframe_new_interpolation_type", text="")
        row.prop(context.user_preferences.edit, "keyframe_new_handle_type", text="")


        row = layout.row()
        row.separator()

        row = layout.row()
        row.label(text="Playback")
        row = layout.row()
        row.prop(context.scene, "sync_mode", text="")
        row.prop(context.scene, "frame_current", text="Frame")
        row.prop(context.scene.render, "fps", text="FPS")
        row = layout.row()
        row.prop(context.scene, "frame_start", text="Start")
        row.prop(context.scene, "frame_end", text="End")


        row = layout.row()
        row.separator()

        row = layout.row()
        row.prop(context.scene.render, "use_simplify", text="Simplify")
        row.prop(context.scene.render, "simplify_subdivision", text="levels")




def register():
    bpy.utils.register_class(le_animation_tools_ui)

def unregister():
    bpy.utils.unregister_class(le_animation_tools_ui)

if __name__ == "__main__":
    register()
