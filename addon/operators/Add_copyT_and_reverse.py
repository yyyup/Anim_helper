import bpy

class Anim_H_Copy_T(bpy.types.Operator):
    """locks shoulder rotation for FK chain"""

    bl_idname = "anim_h.copy_t"
    bl_label = "add copyT reverse"
    bl_description = "reverse the Transform of the bone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the selected bones in pose mode
        selected_bones = bpy.context.selected_pose_bones
        
        # Check if any bones are selected
        if selected_bones is None or len(selected_bones) == 0:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}
        
          # Identify the minimum and maximum keyframes among the selected bones
        min_frame = float('inf')
        max_frame = float('-inf')
        for bone in selected_bones:
            action = bone.id_data.animation_data.action if bone.id_data.animation_data else None
            if action:
                for fcurve in action.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        min_frame = min(min_frame, keyframe.co.x)
                        max_frame = max(max_frame, keyframe.co.x)

        if min_frame == float('inf') or max_frame == float('-inf'):
            self.report({'WARNING'}, "No keyframes found in the selected bones.")
            return {'CANCELLED'}
        
        # Check if valid keyframes were found
        if min_frame == float('inf') or max_frame == float('-inf'):
            self.report({'WARNING'}, "No keyframes found.")
            return {'CANCELLED'}
        
        min_frame = int(min_frame)
        max_frame = int(max_frame)
        

        # Create an empty list to store the created empties
        created_empties = []

        # Loop through each selected bone
        for bone in selected_bones:
            # Create an empty at the location of the bone
            empty = bpy.data.objects.new("Empty", None)
            empty.location = bone.matrix.to_translation()
            
            # Link the empty object to the current scene collection
            bpy.context.collection.objects.link(empty)

            # Get the armature that contains the selected bone
            armature = bone.id_data

            # Add a copy transform constraint to the empty
            constraint = empty.constraints.new(type="COPY_TRANSFORMS")
            constraint.target = armature
            constraint.subtarget = bone.name

            # Add the created empty to the list
            created_empties.append(empty)

        # Store the active object
        original_active_object = bpy.context.active_object

        # Set the active object to the armature and switch to object mode
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Select the created empties and set the first one as the active object
        for empty in created_empties:
            empty.select_set(True)
        bpy.context.view_layer.objects.active = created_empties[0]

        # Bake the action with the specified options
        bpy.ops.nla.bake(
            frame_start=min_frame,
            frame_end=max_frame,
            only_selected=True,
            visual_keying=True,
            clear_constraints=True,
            use_current_action=True,
            bake_types={"OBJECT"}
        )

        # Set the original active object back and switch back to pose mode
        bpy.context.view_layer.objects.active = original_active_object
        bpy.ops.object.mode_set(mode='POSE')

        # Add the Copy Transforms constraint to the original selected bones
        for i, bone in enumerate(selected_bones):
            # Get the corresponding baked empty
            empty = created_empties[i]

            # Add a Copy Transforms constraint to the bone
            constraint = bone.constraints.new(type="COPY_TRANSFORMS")
            constraint.target = empty
        
        
            
        return {'FINISHED'}

