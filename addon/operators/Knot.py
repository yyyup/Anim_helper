import bpy

class ANIM_H_knot(bpy.types.Operator):
    bl_idname = "object.create_empty_and_constraints"
    bl_label = "knot"
    bl_description = "Creates an empty object to control a pose bone with constraints"
    
    def execute(self, context):
        # Ensure we have an active object
        if bpy.context.object is None:
            self.report({'ERROR'}, "Please select an object (mesh, empty, or armature).")
            return {'CANCELLED'}

        active_obj = bpy.context.object

        if active_obj.type in {'MESH', 'EMPTY'}:
            # For mesh or empty objects, create a controlling empty
            bpy.ops.object.empty_add(type='PLAIN_AXES')
            control_empty = bpy.context.object
            control_empty.name = f"Control_{active_obj.name}"

            # Set the empty's transform to match the active object
            control_empty.matrix_world = active_obj.matrix_world

            # Add Copy Location and Copy Rotation constraints to the active object
            bpy.context.view_layer.objects.active = active_obj

            copy_location = active_obj.constraints.new(type='COPY_LOCATION')
            copy_location.target = control_empty

            copy_rotation = active_obj.constraints.new(type='COPY_ROTATION')
            copy_rotation.target = control_empty

            self.report({'INFO'}, f"Control empty '{control_empty.name}' created and linked to object '{active_obj.name}'.")
            return {'FINISHED'}

        elif active_obj.type == 'ARMATURE':
            # Check if a pose bone is selected
            pose_bone = bpy.context.active_pose_bone

            if pose_bone is None:
                self.report({'ERROR'}, "No active pose bone selected.")
                return {'CANCELLED'}

            # Get the bone name
            bone_name = pose_bone.name

            # Create an empty object
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.empty_add(type='PLAIN_AXES')
            control_obj = bpy.context.object
            control_obj.name = f"Empty_{bone_name}"

            # Parent the empty to the armature object for organizational purposes
            control_obj.parent = active_obj

            # Set the empty to the bone's position and orientation
            control_obj.matrix_world = active_obj.matrix_world @ pose_bone.matrix

            # Add a Copy Transforms constraint to the empty
            bpy.context.view_layer.objects.active = control_obj
            bpy.ops.object.constraint_add(type='COPY_TRANSFORMS')
            copy_transforms = control_obj.constraints[-1]
            copy_transforms.target = active_obj
            copy_transforms.subtarget = bone_name

            # Apply the Copy Transforms constraint
            bpy.ops.object.visual_transform_apply()
            control_obj.constraints.remove(copy_transforms)

            # Switch back to Pose Mode
            bpy.context.view_layer.objects.active = active_obj
            bpy.ops.object.mode_set(mode='POSE')

            # Add Copy Location and Copy Rotation constraints to the pose bone
            copy_location = pose_bone.constraints.new(type='COPY_LOCATION')
            copy_location.target = control_obj

            copy_rotation = pose_bone.constraints.new(type='COPY_ROTATION')
            copy_rotation.target = control_obj

            self.report({'INFO'}, f"Control object '{control_obj.name}' created and linked to pose bone '{bone_name}'.")
            return {'FINISHED'}

        else:
            self.report({'ERROR'}, "Unsupported object type. Please select a mesh, empty, or armature.")
            return {'CANCELLED'}