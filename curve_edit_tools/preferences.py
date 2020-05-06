import bpy

class CURVE_OT_insert_bezier_spline_points(bpy.types.AddonPreferences):
    bl_idname = __package__

    snap_to: bpy.props.EnumProperty(
        name="Snap To",
        items = [
            ('SEGMENT', 'Segment', 'Use only the segment, which the mouse had hovered over.'),
            ('SINGLE', 'Single Spline', 'Snap along all of a single spline.'),
            ('ALL', 'All', 'Snap to any curve of the object.')],
        default='SINGLE',
        )
    samples: bpy.props.IntProperty(
            name="Samples",
            description="Number of rough samples between two bezier control point. Increase for accuracy, decrease for speed. Used for the brute force algorithm, which determines the distance to the mouse.",
            default=13,
            )
    epsilon: bpy.props.FloatProperty(
            name="Epsilon",
            description="Distance of the final samples. Decrease, if the inserted point seems stepped. Increase, for speed.",
            default=0.008,
            precision=4,
            step=10
            )
    single_select: bpy.props.EnumProperty(
        name="Spline",
        items = [
            ('CLOSEST', '3D Closest', 'Use the spline closest to the mouse.'),
            ('ACTIVE', 'Active', 'Use the active spline.')],
        default='ACTIVE',
        )
    segment_select: bpy.props.EnumProperty(
        name="Segment",
        items = [
            ('CLOSEST', '2D Closest', 'Use the segment closest to the mouse.'),
            ('SELECTED', 'Select', 'Use the selected segment.')],
        default='CLOSEST',
        )

    def draw(self, context):
        layout = self.layout
        layout.row().label(text="Picking uses a brute force algorithm.")
        row = layout.row()
        row.column().prop(self, "snap_to")
        if (self.snap_to != "ALL"):
            row.column().row().prop(self, "single_select")
        else:
            row.column().label(text="")
        if (self.snap_to == "SEGMENT"):
            row.column().row().prop(self, "segment_select")
        else:
            row.column().label(text="")

        split = layout.split()
        col = split.column()
        col.row().label(text="If speed is prioritized, use ...")
        col.row().label(text="'Active Spline', low Samples, high Epsilon")
        col = split.column()
        col.row().prop(self, "samples")
        col.row().prop(self, "epsilon")