import bpy
import bpy.props

class AH_ApplyPose(bpy.types.Operator):
    """Apply a pose from the active object's pose library"""
    bl_idname = "anim.apply_pose"
    bl_label = "Apply Pose"
    bl_description = "Apply a pose from the active object's pose library"
    bl_options = {'REGISTER', 'UNDO'}

    pose_name: bpy.props.StringProperty(name="Pose Name", default="")

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'ARMATURE' and obj.pose_library is not None

    def execute(self, context):
        obj = context.object
        pose_lib = obj.pose_library
        index = -1
        for i, marker in enumerate(pose_lib.pose_markers):
            if marker.name == self.pose_name:
                index = i
                break
        if index == -1:
            self.report({'ERROR'}, f"Pose '{self.pose_name}' not found")
            return {'CANCELLED'}
        bpy.ops.poselib.apply_pose(pose_index=index)
        self.report({'INFO'}, f"Applied pose '{self.pose_name}'")
        return {'FINISHED'}
