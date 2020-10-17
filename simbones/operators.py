import bpy
import bgl
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import region_2d_to_location_3d

from mathutils import Vector, Quaternion, Euler, Matrix
import math

import importlib
pendulum = importlib.import_module('.pendulum', package=__package__)
Pendulum = getattr(pendulum, 'Pendulum')


def get_matrices_single_bone(ob, pose_bone, edit_bone, frames):
    use_quaternions = pose_bone.rotation_mode == 'QUATERNION'
    transforms = {
        'loc': { 'count': 3, 'path': 'location', 'object': pose_bone.location },
        'rot': {
            'count': 4 if use_quaternions else 3,
            'path': 'rotation_quaternion' if use_quaternions else 'rotation_euler',
            'object': pose_bone.rotation_quaternion if use_quaternions else pose_bone.rotation_euler
            },
        'sca': { 'count': 3, 'path': 'scale', 'object': pose_bone.scale },
    }

    if ob.animation_data == None:
        ob.animation_data_create()

    for key, value in transforms.items():
        result = dict(zip(frames, [value['object'].copy() for f in frames]))

        for i in range(value['count']):
            if ob.animation_data.action:
                crv = ob.animation_data.action.fcurves.find('pose.bones["'
                    + pose_bone.name + '"].' + value['path'], index=i)
            else:
                crv = None
            if crv != None:
                for f in frames:
                    v = crv.evaluate(f)
                    result[f][i] = crv.evaluate(f)
        transforms[key] = result
    
    if use_quaternions:
        for quat in transforms['rot'].values():
            quat.normalize()

    loc, rot, sca = transforms.values()
    matrices = [ Matrix.Translation(loc[frame])
                @ rot[frame].to_matrix().to_4x4()
                @ Matrix.Diagonal(sca[frame]).to_4x4()
        for frame in loc ]
    
    return matrices

def get_matrices(ob, pose_bone, edit_bone, frames):
    base_mat = edit_bone.matrix_local.to_4x4()
    base_mat = [base_mat.copy() for f in frames]
    while pose_bone != None:
        rest_mat = edit_bone.matrix_local.to_4x4()
        rest_mat_inv = rest_mat.inverted()
        matrices = get_matrices_single_bone(ob, pose_bone, edit_bone, frames)
        for i, mat in enumerate(matrices):
            base_mat[i] = rest_mat @ mat @ rest_mat_inv @ base_mat[i]

        pose_bone = pose_bone.parent
        edit_bone = edit_bone.parent
    return base_mat

def get_gravity(scene):
    if scene.simboneworld.use_scene_gravity:
        return scene.gravity
    else:
        return scene.simboneworld.gravity

def bone_quat_to_dir(quat):
    v = Vector((0, 1, 0))
    v.rotate(quat)
    return v

def get_scene_frames(scene):
    start, end1 = scene.frame_start, scene.frame_end + 1
    frames = range(start, end1)
    frame_step = 1 / scene.render.fps
    return frames, frame_step

def simbone_bake(ob, pose_bone, edit_bone, scene):
    frames, frame_step = get_scene_frames(scene)
    
    matrices = get_matrices(ob, pose_bone, edit_bone, frames)
    end_mats = get_matrices_single_bone(ob, pose_bone, edit_bone, frames)
    
    # Main lists.
    positions = [mat.decompose()[0]  * scene.simboneworld.spaceScale
        for mat in matrices]
    orientations = [(matrices[i] @ end_mats[i].inverted()).decompose()[1]
        for i in range(len(end_mats))]

    velocities = [(positions[i] - positions[max(0, i - 1)]) / frame_step
        for i in range(len(positions))]
    accelerations = [(velocities[i] - velocities[max(0, i - 1)]) / frame_step
        for i in range(len(velocities))]

    gravity = get_gravity(scene)
    custom_force = pose_bone.simbone.custom_force.copy()
    up_quat = Euler((pose_bone.simbone.up_offset - 90, 0, 0)).to_quaternion()
    start_dir = bone_quat_to_dir(matrices[0].decompose()[1])

    # Setup pendulum values.
    pen = Pendulum()
    pen.l = edit_bone.length * scene.simboneworld.spaceScale
    pen.m = pose_bone.simbone.m
    pen.set_coords(start_dir)
    pen.c_a = pose_bone.simbone.c_a
    pen.c_d = pose_bone.simbone.c_d

    datapath = 'pose.bones["' + pose_bone.name + '"].rotation_quaternion'
    pose_bone.rotation_mode = 'QUATERNION'
    pose_bone.rotation_quaternion = end_mats[0].decompose()[1]
    pose_bone.keyframe_insert(data_path='rotation_quaternion', frame=frames[0])
    fcurves = [ob.animation_data.action.fcurves.find(datapath, index=i)
        for i in range(4)]

    for i in range(1, len(matrices)):
        matrix = matrices[i]
        frame = frames[i]
        g = gravity.copy()
        f = custom_force.copy()
        f.rotate(orientations[i])

        pen.w = scene.simboneworld.wind - velocities[i]
        pen.f = g + f - accelerations[i]

        pen.do_steps(frame_step * scene.simboneworld.timeScale, 1)
        direction = Vector(pen.get_coords())

        direction.rotate(orientations[i].inverted())
        direction.rotate(up_quat.inverted())
        orient = direction.to_track_quat('Y', 'Z')
        orient.rotate(up_quat)
        
        for i in range(4):
            fcurves[i].keyframe_points.insert(frame, orient[i])

def get_pose_bone_selection(context):
    edit_bones = []
    if context.mode == 'POSE':
        edit_bones.extend([b for b in context.object.data.bones if b.select])
    elif context.mode == 'POSE':
        edit_bones.extend(context.object.data.bones)

    edit_bones.sort(key=lambda b: len(b.parent_recursive))
    return edit_bones

class BoneSimulationOp(bpy.types.Operator):
    bl_options = { 'REGISTER', 'UNDO' }

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.object != None and context.object.type == 'ARMATURE'

class AlignCustomForce(BoneSimulationOp, bpy.types.Operator):
    bl_idname = "pose.simbones_align_custom_force"
    bl_label = "Align Custom Force of Simbones"
    bl_description = "Align the custom force of simbones with their current orientation"

    def execute(self, context):
        edit_bones = get_pose_bone_selection(context)
        for edit_bone in edit_bones:
            pose_bone = context.object.pose.bones[edit_bone.name]
            quat = edit_bone.matrix_local.decompose()[1]
            direction = bone_quat_to_dir(quat) 
            
            custom_force = pose_bone.simbone.custom_force
            
            if (custom_force.length == 0 or
                (direction.x == 0 and direction.y == 0)):
                self.report({'INFO'}, edit_bone.name + " has no magnitude.")
                continue

            custom_force.rotate(quat)

            bone_angles = Pendulum.cartesian_to_sphere(direction)
            force_angles = Pendulum.cartesian_to_sphere(custom_force)
            new_dir = Vector(Pendulum.sphere_to_cartesian(force_angles[0], bone_angles[1]))
            custom_force = new_dir * custom_force.length
            test = Pendulum.cartesian_to_sphere(custom_force)
            custom_force.rotate(quat.inverted())
            pose_bone.simbone.custom_force = custom_force

        return { 'FINISHED' }

class ScaleCustomForce(BoneSimulationOp, bpy.types.Operator):
    bl_idname = "pose.simbones_scale_custom_force"
    bl_label = "Scale Custom Force of Simbones"
    bl_description = "Scale the custom force of simbones to counteract gravity. As a result, the simbone will not move in their rest pose. This will only work with aligned simbones"
    
    def execute(self, context):
        gravity = get_gravity(context.scene)
        edit_bones = get_pose_bone_selection(context)
        for edit_bone in edit_bones:
            quat = edit_bone.matrix_local.decompose()[1]
            direction = bone_quat_to_dir(quat)
            θ, φ = Pendulum.cartesian_to_sphere(direction)

            pose_bone = context.object.pose.bones[edit_bone.name]
            custom_force = pose_bone.simbone.custom_force.copy()
            custom_force.rotate(quat)
            cθ, cφ = Pendulum.cartesian_to_sphere(custom_force)

            if custom_force.length == 0:
                self.report({'WARNING'}, edit_bone.name + ": Force has no magnitude.")
                continue
            if ((direction.x == 0 and direction.y == 0) or
                (custom_force.x == 0 and custom_force.y == 0)):
                self.report({'WARNING'}, edit_bone.name + ": The direction and custom force need an XZ magnitude.")
                continue
            if cθ <= θ:
                self.report({'WARNING'}, edit_bone.name + ": The custom force direction needs to be higher than the bone's rest direction.")
                continue
            
            strength = -gravity[2] * math.sin(θ) / math.sin(cθ - θ)
            pose_bone.simbone.custom_force *= strength / pose_bone.simbone.custom_force.length

        return { 'FINISHED' }
        
def draw_callback(self):
    #bgl.glDisable(bgl.GL_DEPTH_TEST)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glDepthFunc(bgl.GL_ALWAYS)

    shader, batch = self.shader, self.batch
    bgl.glLineWidth(2)
    shader.bind()
    shader.uniform_float("color", (0, 2, 1, 1))
    batch.draw(shader)

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    return

class TranslateCustomForce(BoneSimulationOp, bpy.types.Operator):
    bl_idname = "pose.simbones_translate_custom_force"
    bl_label = "Translate Custom Force Simbones"
    bl_description = "Interactively position the custom force in the 3D viewport"
    bl_options = { 'REGISTER', 'UNDO' }

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE'
            and context.space_data.type == 'VIEW_3D'
            and context.object != None
            and context.object.type == 'ARMATURE'
            and context.object.data.bones.active != None
            and context.object.pose.bones[context.object.data.bones.active.name].simbone.active)

    def finish(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.area.header_text_set(None)

    def update_shader_batch(self):
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.batch = batch_for_shader(self.shader, 'LINES', {"pos": [self.vfrom, self.vto]})

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            context.area.header_text_set("WIP")

            new_pos = region_2d_to_location_3d(
                    context.region, 
                    context.space_data.region_3d,
                    (event.mouse_x, event.mouse_y),
                    self.vto0)
            self.offset = new_pos - self.pos
            self.vto = self.vto0 + self.offset
            self.update_shader_batch()

        elif event.type == 'LEFTMOUSE':
            cf = self.vto - self.vfrom
            cf.rotate(self.quat.inverted())
            self.bone.simbone.custom_force = cf
            self.finish(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish(context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.bone = context.object.pose.bones[context.object.data.bones.active.name]
        self.vfrom, self.quat, _ = self.bone.matrix.decompose()
        cf = self.bone.simbone.custom_force.copy()
        cf.rotate(self.quat)
        self.vto = self.vfrom + cf
        self.vto0 = self.vto.copy()
        
        self.pos = region_2d_to_location_3d(
                context.region, 
                context.space_data.region_3d,
                (event.mouse_x, event.mouse_y),
                self.vto0)

        self.update_shader_batch()
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, (self,), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        print("called execute")
        return {'FINISHED'}
        



class BakeBoneSimulation(bpy.types.Operator):
    bl_idname = "pose.simbones_bake"
    bl_label = "Bake Simbones"
    bl_description = "Bake the movement of simbones to keyframes. Bakes all simbones in Object Mode and selected simbones in Pose Mode"
    bl_options = { 'REGISTER', 'UNDO' }

    @classmethod
    def poll(cls, context):
        return (context.object != None and context.object.type == 'ARMATURE' and
            (context.mode == 'OBJECT' or context.mode == 'POSE'))

    def execute(self, context):
        edit_bones = get_pose_bone_selection(context)
        
        for edit_bone in edit_bones:
            pose_bone = context.object.pose.bones[edit_bone.name]
            if pose_bone.simbone.active:
                simbone_bake(context.object, pose_bone, edit_bone, context.scene)
        
        self.report({'INFO'}, "Baked Simbones: "  + ", ".join([b.name for b in edit_bones]))
        return { 'FINISHED' }


classes = (
    TranslateCustomForce,
    BakeBoneSimulation,
    AlignCustomForce,
    ScaleCustomForce,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)



def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)