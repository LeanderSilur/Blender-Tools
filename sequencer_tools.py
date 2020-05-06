bl_info = {
    "name": "Sequencer Tools",
    "description": "Tools and shortcuts for the VSE.",
    "author": "Arun Lenader",
    "version": (0, 1),
    "blender": (2, 78, 0),
    "location": "",
    "support": "TESTING",
    "category": "Sequencer"
}

from bpy import context
from bpy import ops
import bpy

def leCutAsEnd(strip, frame):
    strip.frame_final_end = frame
def leCutToNext():
    scene = context.scene
    seq = scene.sequence_editor.sequences
    
    frame = scene.frame_current
    seq = sorted(seq, key = lambda x: x.frame_final_start)
    
    print(frame)
    for s in seq:
        if (frame <= s.frame_final_start):
            break
        if (frame <= s.frame_final_end):
            leCutAsEnd(s, frame)
            print("Cut a strip.")
    ops.sequencer.gap_remove()
class LeCutToNext(bpy.types.Operator):
    """Cut To Next Script"""
    bl_idname = "le_seq.cut_to_next"
    bl_label = "Cut To Next"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.
    def execute(self, context):
        leCutToNext()
        return {'FINISHED'}

################################

class LeExtendUnit(bpy.types.Operator):
    """Extends the current strips and moves all following strips"""
    bl_idname = "le_seq.extend_unit"
    bl_label = "Extend Unit"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.
    def execute(self, context):
        i = 50
        ops.sequencer.gap_insert(frames = i)
        scene = context.scene
        seq = scene.sequence_editor.sequences
        
        frame = scene.frame_current
        seq = sorted(seq, key = lambda x: x.frame_final_start)
        
        print(frame)
        for s in seq:
            if (frame <= s.frame_final_start):
                break
            if (frame <= s.frame_final_end) and (s.type != "SOUND"):
                s.frame_final_end = s.frame_final_end + i
        return {'FINISHED'}


def register():
    bpy.utils.register_class(LeCutToNext)
    bpy.utils.register_class(LeExtendUnit)
def unregister():
    bpy.utils.unregister_class(LeCutToNext)
    bpy.utils.unregister_class(LeExtendUnit)
if __name__ == "__main__":
    register()