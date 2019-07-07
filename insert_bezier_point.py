bl_info = {
    "name": "Insert Bezier Point",
    "category": "Curve",
    "description": "Select two points of a bezier curve and press I to insert another bezier point between them.",
    "author": "Arun Leander"
}
import bpy
import bgl
import blf
import numpy as np
import math
import mathutils



class CubicBezier(object):
    def __init__(self, points):
        self.points = np.array(points).astype(np.float32)

    def at(self, t):
        pt =  1 *        (1 - t)**3 * self.points[0]
        pt += 3 * t**1 * (1 - t)**2 * self.points[1]
        pt += 3 * t**2 * (1 - t)**1 * self.points[2]
        pt += 1 * t**3              * self.points[3]
        return pt

    def split(self, t):
        p1, p2, p3, p4 = self.points
        
        p12 = (p2-p1)*t+p1
        p23 = (p3-p2)*t+p2
        p34 = (p4-p3)*t+p3
        p123 = (p23-p12)*t+p12
        p234 = (p34-p23)*t+p23
        p1234 = (p234-p123)*t+p123

        return [p1,p12,p123,p1234,p234,p34,p4]

def gl_end_and_restore():
    bgl.glEnd()
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    bgl.glPointSize(1)
    
def draw_callback_bezier_2d(self, context):
    bgl.glEnable(bgl.GL_BLEND)

    font_id = 0
    blf.position(font_id, (context.area.width-84)/2, context.area.height / 8 * 7, 0)
    blf.size(font_id, 12, 72)
    blf.draw(font_id, "Inserting Point: " + str(at))
    
    gl_end_and_restore()
    
def draw_callback_bezier_3d(self, context):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glDepthFunc(bgl.GL_ALWAYS)

    
    split = self.bezier.split(self.at)
    points = self.bezier.points
    
    bgl.glColor4f(1,1,1,0.5)
    bgl.glLineWidth(1.0)
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex3f(*points[0])
    bgl.glVertex3f(*points[1])
    bgl.glVertex3f(*points[2])
    bgl.glVertex3f(*points[3])
    bgl.glEnd()
    
    bgl.glColor4f(1,1,1,1)
    bgl.glPointSize(6)
    bgl.glBegin(bgl.GL_POINTS)
    bgl.glVertex3f(*points[0])
    bgl.glVertex3f(*points[3])
    bgl.glEnd()
    
    bgl.glPointSize(2)
    bgl.glBegin(bgl.GL_POINTS)
    bgl.glVertex3f(*points[1])
    bgl.glVertex3f(*points[2])
    bgl.glEnd()
    
    # draw new bezier anchor
    bgl.glColor4f(0.8, 1.0, 0.0, 0.5)
    bgl.glLineWidth(2)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex3f(*split[2])
    bgl.glVertex3f(*split[3])
    bgl.glVertex3f(*split[4])
    bgl.glEnd()
    
    bgl.glColor4f(0.2,1,0.0, 1.0)
    bgl.glPointSize(10)
    bgl.glBegin(bgl.GL_POINTS)
    bgl.glVertex3f(*split[3])
    bgl.glEnd()
    
    bgl.glPointSize(6)
    bgl.glBegin(bgl.GL_POINTS)
    bgl.glVertex3f(*split[2])
    bgl.glVertex3f(*split[4])
    bgl.glEnd()
    
    gl_end_and_restore()


class InsertBezierPoint(bpy.types.Operator):
    """Insert a point between two other bezier spline keypoints."""
    bl_idname = "curve.insert_bezier_spline_point"
    bl_label = "Insert Bezier Point"
    

        
    def create_new_spline(self, context):
        spline = self.ob.data.splines.active
        spline.bezier_points.add()

        split = self.bezier.split(self.at)
        self.points[self.insert_at][2] = split[1]
        self.points.insert(self.insert_at + 1, split[2:5])
        self.points[self.insert_at + 2][0] = split[5]
        
        for i in range(len(self.points)):
            point = self.points[i]
            select = i == self.insert_at + 1
            spline.bezier_points[i].select_control_point = select
            spline.bezier_points[i].select_right_handle = select
            spline.bezier_points[i].select_left_handle = select
            
            spline.bezier_points[i].handle_left = mathutils.Vector(point[0])
            spline.bezier_points[i].co = mathutils.Vector(point[1])
            spline.bezier_points[i].handle_right = mathutils.Vector(point[2])
        bpy.ops.transform.translate('INVOKE_DEFAULT', True)
            
        
    def exit_handler(self):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
        self.ob.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        
    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}
        elif event.type == 'MOUSEMOVE':
            self.mouse_x = event.mouse_x
            self.at = ((self.mouse_x - context.area.x) / context.area.width)

        elif event.type in {'LEFTMOUSE', 'NUMPAD_ENTER', 'RET'}:
            self.exit_handler()
            self.create_new_spline(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.exit_handler()
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "Execute the operator in the VIEW3D.")
            return {'CANCELLED'}
        
        if (context.object == None or
            context.object.type != 'CURVE' or
            context.object.data.is_editmode == False):
            self.report({'WARNING'}, "Select a curves points in edit mode.")
            return {'CANCELLED'}
        
        self.ob = context.object
        
        spline = self.ob.data.splines.active
        for i in range(len(spline.bezier_points)):
            # check if the point is selected
            # if the user is aware, the next point will be selected as well
            if spline.bezier_points[i].select_control_point:
                # check if the 2nd points exists
                if i + 1 >= len(spline.bezier_points):
                    self.report({'WARNING'}, "Select TWO points of the bezier curve.")
                    return {'CANCELLED'}
                
                self.insert_at = i
                self.points = []
                # "deep clone" the curve
                for point in spline.bezier_points:
                    self.points.append([point.handle_left.copy(), point.co.copy(), point.handle_right.copy()])
                    
                bezier_points = [self.points[i][1],
                                self.points[i][2],
                                self.points[i+1][0],
                                self.points[i+1][1]]
                self.bezier = CubicBezier(bezier_points)
                self.original_mouse_position = event.mouse_x, event.mouse_y
                self.mouse_x = event.mouse_x
                self.at = 0
                break
        
        args = (self, context)            
        self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_bezier_2d, args, 'WINDOW', 'POST_PIXEL')
        self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_bezier_3d, args, 'WINDOW', 'POST_VIEW')


        context.window_manager.modal_handler_add(self)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.ob.select = False
        return {'RUNNING_MODAL'}
    

# store keymaps here to access after registration
addon_keymaps = []

def register():
    bpy.utils.register_class(InsertBezierPoint)
    
    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either,
    # so we have to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Curve', space_type='EMPTY')
        kmi = km.keymap_items.new(InsertBezierPoint.bl_idname, 'I', 'PRESS')
        addon_keymaps.append((km, kmi))


def unregister():
    
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    bpy.utils.unregister_class(InsertBezierPoint)

if __name__ == "__main__":
    register()
