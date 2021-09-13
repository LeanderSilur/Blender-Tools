import bpy
import bgl
import gpu
import math
import mathutils
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader
import importlib

bezier_py = importlib.import_module('.bezier', package=__package__)
CubicBezier = getattr(bezier_py, 'CubicBezier')


shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

def draw_callback_bezier_3d(self, context):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glDepthFunc(bgl.GL_ALWAYS)

    bezier = self.beziers[self.spline_id][self.bezier_id]
    split = bezier.split(self.at)
    points = bezier.points

    bgl.glLineWidth(1.0)
    shader.bind()
    shader.uniform_float("color", (1, 1, 1, 0.5))
    batch = batch_for_shader(shader, 'LINES', {"pos": points})
    batch.draw(shader)

    bgl.glPointSize(6)
    shader.uniform_float("color", (1, 1, 1, 1))
    batch = batch_for_shader(shader, 'POINTS', {"pos": [points[0], points[3]]})
    batch.draw(shader)

    bgl.glPointSize(2)
    batch = batch_for_shader(shader, 'POINTS', {"pos": [points[1], points[2]]})
    batch.draw(shader)

    # draw new bezier anchor
    bgl.glLineWidth(2)
    shader.uniform_float("color", (0.8, 1.0, 0.0, 0.5))
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [split[2], split[3], split[4]]})
    batch.draw(shader)

    bgl.glPointSize(10)
    shader.uniform_float("color", (0.2, 1, 0.0, 1.0))
    batch = batch_for_shader(shader, 'POINTS', {"pos": [split[3]]})
    batch.draw(shader)

    bgl.glPointSize(6)
    batch = batch_for_shader(shader, 'POINTS', {"pos": [split[2], split[4]]})
    batch.draw(shader)

    # gl end and restore
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    bgl.glPointSize(1)

class InsertBezierPoint(bpy.types.Operator):
    """Insert a point between existing bezier spline keypoints."""
    bl_idname = "curve.insert_bezier_spline_point"
    bl_label = "Insert Bezier Point"
    bl_description = "Insert a bezier point on an existing bezier spline."
    bl_options = { 'REGISTER', 'UNDO' }
    
    def point_in_view(self, context, point3d):
        point2d = location_3d_to_region_2d(context.region, context.region_data, point3d)
        if (point2d[0] >= 0 and point2d[1] >= 0 and
            point2d[0] < context.region.width and point2d[1] < context.region.height):
            return True
        return False

    def get_2d_distance(self, context, point3d, mouse_pos):
        point2d = location_3d_to_region_2d(context.region, context.region_data, point3d)
        
        if (point2d.x >= 0 and point2d.y >= 0 and
            point2d.x < context.region.width and point2d.y < context.region.height):
            distance = (point2d - mouse_pos).length
            return distance
        return math.inf

    def get_3d_closest(self, context):
        samples = self.addon_prefs.samples

        spaceview3d = context.area.spaces[0]
        view_mat = spaceview3d.region_3d.view_matrix
        is_perspective = spaceview3d.region_3d.is_perspective

        points = []
        for a in range(self.a0, self.a1):
            for b in range(len(self.beziers[a])):
                bezier = self.beziers[a][b]
                for i in range(0, samples + 1):
                    point3d = bezier.at(i/samples)
                    vec = mathutils.Vector(point3d)

                    if self.point_in_view(context, vec):

                        if is_perspective:
                            points.append([a, b, (view_mat @ vec).length])
                        else:
                            points.append([a, b, -(view_mat @ vec).z])
        
        if len(points) == 0:
            return -1, -1

        # use a lamda expression to get closest point
        return min(points, key = lambda x: x[2])[0:2]


    def get_2d_closest(self, context, event):
        mouse_pos = mathutils.Vector((event.mouse_x - context.region.x, event.mouse_y  - context.region.y))
        
        distance = math.inf
        
        mindex = None
        at = 0
        samples = self.addon_prefs.samples

        for a in range(self.a0, self.a1):
            b0 = 0
            b1 = len(self.beziers[a])
            if self.b >= 0:
                b0 = self.b
                b1 = b0 + 1

            for b in range(b0, b1):
                bezier = self.beziers[a][b]
                for i in range(1, samples):

                    point3d = bezier.at(i/samples)
                    new_distance = self.get_2d_distance(context, point3d, mouse_pos)
                    if (new_distance < distance):
                        distance = new_distance
                        mindex = a, b
                        at = i


        bezier = self.beziers[mindex[0]][mindex[1]]
        index_a = (at-1)/samples
        index_b = (at+1)/samples
        pt_a = location_3d_to_region_2d(context.region, context.region_data, bezier.at(index_a))
        pt_b = location_3d_to_region_2d(context.region, context.region_data, bezier.at(index_b))
        distance_a = (pt_a - mouse_pos).length
        distance_b = (pt_b - mouse_pos).length
        difference = abs(distance_a - distance_b)
        
        while (difference > self.EPSILON):
            i += 1
            if (distance_a > distance_b):
                distance_a, distance_b = distance_b, distance_a
                pt_a, pt_b = pt_b, pt_a
                index_a, index_b = index_b, index_a
            index_b = (index_a + index_b) / 2
            pt_b = location_3d_to_region_2d(context.region, context.region_data, bezier.at(index_b))
            distance_b = (pt_b - mouse_pos).length
            difference = abs(distance_a - distance_b)
        return [*mindex, index_a]
        
    def create_new_spline(self, context):
        spline = self.ob.data.splines[self.spline_id]
        spline_points = spline.bezier_points
        spline_points.add(1)

        split = self.beziers[self.spline_id][self.bezier_id].split(self.at)

        # loop from the end backwards and replace positions
        for i in range(len(spline_points)-2, self.bezier_id, -1):
            spline_points[i+1].co           = spline_points[i].co 
            spline_points[i+1].handle_right = spline_points[i].handle_right
            spline_points[i+1].handle_left  = spline_points[i].handle_left
            
            spline_points[i+1].handle_right_type = spline_points[i].handle_right_type
            spline_points[i+1].handle_left_type  = spline_points[i].handle_left_type

        i = self.bezier_id - len(spline_points)
        
        spline_points[i + 1].handle_right_type = 'ALIGNED'
        spline_points[i + 1].handle_left_type  = 'ALIGNED'
        
        mat = self.ob.matrix_world.inverted()
        spline_points[i    ].handle_right = mat @ mathutils.Vector(split[1])
        spline_points[i + 1].co =           mat @ mathutils.Vector(split[3])
        spline_points[i + 1].handle_left  = mat @ mathutils.Vector(split[2])
        spline_points[i + 1].handle_right = mat @ mathutils.Vector(split[4])
        spline_points[i + 2].handle_left  = mat @ mathutils.Vector(split[5])

        spline_points[i + 1].select_control_point = True
        spline_points[i + 1].select_right_handle = True
        spline_points[i + 1].select_left_handle = True
    
    def beziers_from_splines(self, splines, mat):
        beziers = []
        for spline in splines:
            spline_beziers = []

            pt_count = len(spline.bezier_points)
            for i in range(pt_count if spline.use_cyclic_u else pt_count - 1):
                
                bezier_points = [   mat @ spline.bezier_points[i].co,
                                    mat @ spline.bezier_points[i].handle_right,
                                    mat @ spline.bezier_points[i-pt_count + 1].handle_left,
                                    mat @ spline.bezier_points[i-pt_count + 1].co
                                ]
                
                spline_beziers.append(CubicBezier(bezier_points))
            beziers.append(spline_beziers)
        return beziers
        
    def exit_handler(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
        self.ob.select_set(True)
        context.area.header_text_set(None)
        bpy.ops.object.mode_set(mode='EDIT')
        
    
    spline_id: bpy.props.IntProperty(default=0,
        name='Spline Id', options={'HIDDEN'})
    bezier_id: bpy.props.IntProperty(default=0,
        name='Position', options={'HIDDEN'})
    at: bpy.props.FloatProperty(default=0.5,
        name='Position',
        min=0, max=1,
        subtype='FACTOR',
        description='Parametric position between to keypoints.')

    def execute(self, context):
        bpy.ops.curve.select_all(action="DESELECT")
        self.create_new_spline(context)
        return {'FINISHED'}

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}

        elif event.type == 'MOUSEMOVE':
            self.spline_id, self.bezier_id, self.at = self.get_2d_closest(context, event)
            context.area.header_text_set("Insert point at {:.4f}.".format(self.at))

        elif event.type in {'LEFTMOUSE', 'NUMPAD_ENTER', 'RET'}:
            self.exit_handler(context)
            bpy.ops.curve.select_all(action="DESELECT")
            self.create_new_spline(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.exit_handler(context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "Execute the operator in the VIEW3D.")
            return {'CANCELLED'}
        
        if (context.object == None or
            context.object.type != 'CURVE' or
            context.object.data.is_editmode == False or
            len(context.object.data.splines) == 0):
            self.report({'WARNING'}, "Enter the edit mode of a curve.")
            return {'CANCELLED'}
        
        self.ob = context.object
        # convert all splines in to lists of cubic beziers
        splines = self.ob.data.splines
        self.beziers = self.beziers_from_splines(splines, self.ob.matrix_world)

        preferences = context.preferences
        self.addon_prefs = preferences.addons[__package__].preferences
        self.EPSILON = self.addon_prefs.epsilon
        self.a0 = 0
        self.a1 = len(self.beziers)
        self.b = -1

        close_a, close_b = self.get_3d_closest(context)
        close_a = max(close_a, 0)


        # choose spline
        if self.addon_prefs.snap_to != 'ALL':

            if self.addon_prefs.single_select == 'ACTIVE':
                for i in range(len(splines)):
                    if splines[i] == splines.active:
                        self.a0 = i

            if self.addon_prefs.single_select == 'CLOSEST':
                self.a0 = close_a

            self.a1 = self.a0 + 1


        # choose control point
        if self.addon_prefs.snap_to == 'SEGMENT':
            if self.addon_prefs.segment_select == 'SELECTED':
                print("Searching")
                for i in range(len(splines[self.a0].bezier_points) - 1):
                    if splines[self.a0].bezier_points[i].select_control_point:
                        print("FOUND")
                        self.b = i
                        break

            if self.addon_prefs.segment_select == 'CLOSEST':
                closest = self.get_2d_closest(context, event)
                self.b = closest[1]


        # at is a triple [spline_id, bezier_id, bezier_parameter (t)]
        self.spline_id, self.bezier_id, self.at = self.get_2d_closest(context, event)

        self.points2d = []
        
        args = (self, context)            
        self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_bezier_3d, args, 'WINDOW', 'POST_VIEW')
        context.area.header_text_set("Insert point at {:.4f}.".format(self.at))

        context.window_manager.modal_handler_add(self)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.ob.select_set(False)
        return {'RUNNING_MODAL'}