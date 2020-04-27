bl_info = {
    "name": "Weight Paint Brush Selection",
    "author": "Arun Leander",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "Select Weight Paint Brush, a useful operator to assign hotkeys to brushes",
    "warning": "",
    "wiki_url": "",
    "category": "Paint",
}

import bpy

class SelectWeightPaintBrush(bpy.types.Operator):
    bl_idname = "scene.select_weight_paint_brush"
    bl_label = "Select Weight Paint Brush"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty(
        name="brush name",
        default="Add"
    )

    def execute(self, context):
        brush = bpy.data.brushes.get(self.name)
        if brush is None:
            self.report({'ERROR'}, "Brush not found " + self.name)
            return {'FINISHED'}
        context.tool_settings.weight_paint.brush = brush
        return {'FINISHED'}

addon_keymaps = []

def register():
    bpy.utils.register_class(SelectWeightPaintBrush)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Weight Paint', space_type='EMPTY')
    
    kmi = km.keymap_items.new(SelectWeightPaintBrush.bl_idname, 'ONE', 'PRESS')
    kmi.properties.name = 'Add'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(SelectWeightPaintBrush.bl_idname, 'TWO', 'PRESS')
    kmi.properties.name = 'Blur'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(SelectWeightPaintBrush.bl_idname, 'THREE', 'PRESS')
    kmi.properties.name = 'Draw'
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new(SelectWeightPaintBrush.bl_idname, 'FOUR', 'PRESS')
    kmi.properties.name = 'Subtract'
    addon_keymaps.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(SelectWeightPaintBrush)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    

if __name__ == "__main__":
    register()
