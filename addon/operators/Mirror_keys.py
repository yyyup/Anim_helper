import bpy
from mathutils import Quaternion, Euler


def get_or_create_fcurve(action, data_path, index):
    """Return existing fcurve or create a new one."""
    fcurve = action.fcurves.find(data_path, index=index)
    if fcurve is None:
        fcurve = action.fcurves.new(data_path, index=index)
    return fcurve


def calculate_mirrored_value(fcurve, pose_bone, keyframe):
    """Calculate mirrored keyframe value based on property type."""
    if "location" in fcurve.data_path:
        return -keyframe.co[1] if fcurve.array_index == 0 else keyframe.co[1]
    if "rotation_quaternion" in fcurve.data_path:
        return -keyframe.co[1] if fcurve.array_index == 1 else keyframe.co[1]
    if "rotation_euler" in fcurve.data_path:
        euler_rotation = Euler(
            (
                fcurve.evaluate(keyframe.co[0]) if fcurve.array_index == 0 else pose_bone.rotation_euler[0],
                fcurve.evaluate(keyframe.co[0]) if fcurve.array_index == 1 else pose_bone.rotation_euler[1],
                fcurve.evaluate(keyframe.co[0]) if fcurve.array_index == 2 else pose_bone.rotation_euler[2],
            ),
            pose_bone.rotation_mode,
        )
        mirrored_euler = Euler(
            (euler_rotation.x, -euler_rotation.y, -euler_rotation.z),
            pose_bone.rotation_mode,
        )
        if fcurve.array_index == 0:
            return mirrored_euler.x
        if fcurve.array_index == 1:
            return mirrored_euler.y
        return mirrored_euler.z
    return keyframe.co[1]

class AH_MirrorBoneKeyframes(bpy.types.Operator):
    """Mirror keyframes from one bone to its opposite side bone (e.g., from left to right)"""
    bl_idname = "anim.mirror_bone_keyframes"
    bl_label = "Mirror Bone Keyframes"
    bl_description = "Mirror animation from a bone to its opposite side counterpart (.L/.R naming)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Ensure an armature is selected and in pose mode with an active bone
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
            and context.mode == 'POSE'
            and context.active_pose_bone is not None
        )

    def execute(self, context):
        try:
            # Get the active pose bone
            selected_bone = context.active_pose_bone
            selected_bone_name = selected_bone.name

            # Get the armature
            armature = context.active_object.data

            # Check if the selected bone follows the naming convention (.L or .R suffix)
            if not selected_bone_name.endswith((".L", ".R")):
                self.report({'ERROR'}, "Selected bone does not follow the left-right naming convention (.L/.R).")
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
            obj = context.active_object
            if not obj.animation_data or not obj.animation_data.action:
                self.report({'ERROR'}, "No animation data found on the armature.")
                return {'CANCELLED'}
                
            action = obj.animation_data.action

            # Get the selected bone and opposite bone
            pose_bone = obj.pose.bones[selected_bone_name]
            opposite_pose_bone = obj.pose.bones[opposite_bone_name]

            # Store the original rotation mode of the opposite bone
            original_rotation_mode = opposite_pose_bone.rotation_mode

            # Set the opposite bone's rotation mode to match the selected bone
            opposite_pose_bone.rotation_mode = pose_bone.rotation_mode

            # Track mirrored keyframes for reporting
            keyframes_mirrored = 0
            fcurves_created = 0

            # Iterate through all fcurves in the action
            for fcurve in action.fcurves:
                # Check if the fcurve corresponds to the selected bone
                if fcurve.data_path.startswith(f'pose.bones["{selected_bone_name}"].'):
                    # Create the data path for the opposite bone
                    opposite_data_path = fcurve.data_path.replace(selected_bone_name, opposite_bone_name)
                    
                    # Find or create the opposite fcurve
                    opposite_fcurve = get_or_create_fcurve(action, opposite_data_path, fcurve.array_index)
                    if len(opposite_fcurve.keyframe_points) == 0:
                        fcurves_created += 1

                    # Mirror the keyframes
                    for keyframe in fcurve.keyframe_points:
                        mirrored_value = calculate_mirrored_value(fcurve, pose_bone, keyframe)

                        # Add or update the keyframe in the opposite fcurve
                        keypoint = opposite_fcurve.keyframe_points.insert(
                            keyframe.co[0],  # Frame
                            mirrored_value,  # Value
                            options={'FAST'}
                        )
                        
                        # Copy handle and interpolation settings
                        keypoint.handle_left_type = keyframe.handle_left_type
                        keypoint.handle_right_type = keyframe.handle_right_type
                        keypoint.interpolation = keyframe.interpolation
                        
                        keyframes_mirrored += 1

            # Update the fcurves to ensure smooth interpolation
            for fcurve in action.fcurves:
                if fcurve.data_path.startswith(f'pose.bones["{opposite_bone_name}"].'):
                    fcurve.update()

            # Restore the original rotation mode of the opposite bone
            opposite_pose_bone.rotation_mode = original_rotation_mode

            self.report({'INFO'}, f"Mirrored {keyframes_mirrored} keyframes from '{selected_bone_name}' to '{opposite_bone_name}'.")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error mirroring keyframes: {str(e)}")
            return {'CANCELLED'}
