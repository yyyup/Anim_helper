import bpy
from mathutils import Quaternion, Euler

class AH_MIRROR_BONE_KEYFRAMES(bpy.types.Operator):
    """Mirror keyframes of the selected bone to its opposite side bone"""
    bl_idname = "anim.mirror_bone_keyframes"
    bl_label = "Mirror Bone Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Ensure an armature is selected and in pose mode
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
            and context.mode == 'POSE'
            and context.active_pose_bone is not None
        )

    def execute(self, context):
        selected_bone = context.active_pose_bone
        selected_bone_name = selected_bone.name

        # Get the active object (assumed to be an armature)
        obj = context.active_object
        armature = obj.data

        # Check if the selected bone follows the naming convention
        if not selected_bone_name.endswith((".L", ".R")):
            self.report({'ERROR'}, "Selected bone does not follow the left-right naming convention.")
            return {'CANCELLED'}

        # Determine the opposite bone name
        if selected_bone_name.endswith(".L"):
            opposite_bone_name = selected_bone_name[:-2] + ".R"
        else:
            opposite_bone_name = selected_bone_name[:-2] + ".L"

        # Check if the opposite bone exists
        if opposite_bone_name not in armature.bones:
            self.report({'ERROR'}, f"Opposite bone '{opposite_bone_name}' not found.")
            return {'CANCELLED'}

        # Get the action (animation data)
        action = obj.animation_data.action
        if action is None:
            self.report({'ERROR'}, "No animation data found.")
            return {'CANCELLED'}

        # Get the selected bone and opposite bone
        pose_bone = obj.pose.bones[selected_bone_name]
        opposite_pose_bone = obj.pose.bones[opposite_bone_name]

        # Store the original rotation mode of the opposite bone
        original_rotation_mode = opposite_pose_bone.rotation_mode

        # Set the opposite bone's rotation mode to match the selected bone
        opposite_pose_bone.rotation_mode = pose_bone.rotation_mode

        # Iterate through all fcurves in the action
        for fcurve in action.fcurves:
            # Check if the fcurve corresponds to the selected bone
            if fcurve.data_path.startswith(f'pose.bones["{selected_bone_name}"].'):
                # Create a new fcurve for the opposite bone
                opposite_data_path = fcurve.data_path.replace(selected_bone_name, opposite_bone_name)
                opposite_fcurve = action.fcurves.find(opposite_data_path, index=fcurve.array_index)

                # If the opposite fcurve doesn't exist, create it
                if opposite_fcurve is None:
                    opposite_fcurve = action.fcurves.new(opposite_data_path, index=fcurve.array_index)

                # Mirror the keyframes
                for keyframe in fcurve.keyframe_points:
                    # Get the mirrored value
                    if "location" in fcurve.data_path:
                        if fcurve.array_index == 0:  # X-axis
                            mirrored_value = -keyframe.co[1]
                        else:
                            mirrored_value = keyframe.co[1]
                    elif "rotation_quaternion" in fcurve.data_path:
                        # Handle quaternion rotation
                        if fcurve.array_index == 1:  # X component of quaternion
                            mirrored_value = -keyframe.co[1]
                        else:
                            mirrored_value = keyframe.co[1]
                    elif "rotation_euler" in fcurve.data_path:
                        # Handle Euler rotation
                        euler_rotation = Euler((
                            keyframe.co[1] if fcurve.array_index == 0 else pose_bone.rotation_euler[0],
                            keyframe.co[1] if fcurve.array_index == 1 else pose_bone.rotation_euler[1],
                            keyframe.co[1] if fcurve.array_index == 2 else pose_bone.rotation_euler[2]
                        ), pose_bone.rotation_mode)

                        # Mirror the Euler rotation
                        mirrored_euler = Euler((
                            euler_rotation.x,
                            -euler_rotation.y,
                            -euler_rotation.z
                        ), pose_bone.rotation_mode)

                        # Get the mirrored value for the current axis
                        if fcurve.array_index == 0:
                            mirrored_value = mirrored_euler.x
                        elif fcurve.array_index == 1:
                            mirrored_value = mirrored_euler.y
                        elif fcurve.array_index == 2:
                            mirrored_value = mirrored_euler.z
                    else:
                        mirrored_value = keyframe.co[1]

                    # Add or update the keyframe in the opposite fcurve
                    opposite_fcurve.keyframe_points.insert(keyframe.co[0], mirrored_value)

        # Restore the original rotation mode of the opposite bone
        opposite_pose_bone.rotation_mode = original_rotation_mode

        self.report({'INFO'}, f"Keyframes mirrored from '{selected_bone_name}' to '{opposite_bone_name}'.")
        return {'FINISHED'}