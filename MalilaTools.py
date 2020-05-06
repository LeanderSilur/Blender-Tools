bl_info = {
    "name": "MalilaTools",
    "author": "Your Name Here",
    "version": (1, 0),
    "blender": (2, 70, 0),
    "location": "View3D > Object > ",
    "description": "Adds a new Mesh Object",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}

import bpy

class RenameToUnderscoreOperator(bpy.types.Operator):
    """Rename bones by replacing dots with underscores"""
    bl_idname = "addongen.malilatools_renametounderscores"
    bl_label = "Rename Underscore"
    bl_options = {'UNDO','REGISTER'}


    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        if context.object.type != 'ARMATURE':
            return False
        return True
    
    def execute(self, context):
        self.report({'INFO'}, "Renaming . to _")
        rig = bpy.context.object
        for b in rig.data.bones:
            b.name = b.name.replace('.', '_')
        return {'FINISHED'}
    
    #def invoke(self, context, event):
    #    wm.modal_handler_add(self)
    #    return {'RUNNING_MODAL'}  
    #    return wm.invoke_porps_dialog(self)
    #def modal(self, context, event):
    #def draw(self, context):

class MalilaToolsPanel(bpy.types.Panel):
    """Docstring of MalilaToolsPanel"""
    bl_idname = "VIEW3D_PT_malilatools"
    bl_label = "MalilaTools Panel"
    
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Tools'
    
    #Panels in ImageEditor are using .poll() instead of bl_context.
    #@classmethod
    #def poll(cls, context):
    #    return context.space_data.show_paint
    
    def draw(self, context):
        layout = self.layout
        layout.operator(RenameToUnderscoreOperator.bl_idname)

# store keymaps here to access after registration
addon_keymaps = []

def register():
    bpy.utils.register_class(RenameToUnderscoreOperator)
    bpy.utils.register_class(MalilaToolsPanel)
    
    # handle the keymap
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new(RenameToUnderscoreOperator.bl_idname, 'M', 'PRESS', ctrl=True, alt=True)
    #kmi.properties.prop1 = 'some'
    addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(RenameToUnderscoreOperator)
    bpy.utils.unregister_class(MalilaToolsPanel)
    
    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
if __name__ == "__main__":
    register()
