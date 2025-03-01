import bpy

class AH_CopyTransforms(bpy.types.Operator):
    """Create empty objects that copy and can reverse the transforms of selected bones"""
    bl_idname = "anim_h.copy_t"
    bl_label = "Copy Transforms with Reverse"
    bl_description = "Create empties that copy transforms from bones for advanced animation control"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the selected bones in pose mode
        selected_bones = context.selected_pose_bones
        
        # Check if any bones are selected
        if not selected_bones or len(selected_bones) == 0:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}
        
        # Find the keyframe range for the selected bones
        min_frame = float('inf')
        max_frame = float('-inf')
        
        # Check for animation data
        armature = selected_bones[0].id_data
        if not armature.animation_data or not armature.animation_data.action:
            self.report({'WARNING'}, "No animation data found on the armature.")
            return {'CANCELLED'}
            
        # Scan fcurves for keyframe range
        action = armature.animation_data.action
        for bone in selected_bones:
            bone_path = f'pose.bones["{bone.name}"]'
            for fcurve in action.fcurves:
                if bone_path in fcurve.data_path and fcurve.keyframe_points:
                    for keyframe in fcurve.keyframe_points:
                        min_frame = min(min_frame, keyframe.co.x)
                        max_frame = max(max_frame, keyframe.co.x)

        if min_frame == float('inf') or max_frame == float('-inf'):
            self.report({'WARNING'}, "No keyframes found in the selected bones.")
            return {'CANCELLED'}
        
        # Round to integer frames
        min_frame = int(min_frame)
        max_frame = int(max_frame)
        
        # Create empties for the selected bones
        created_empties = []
        try:
            # Create an empty for each selected bone
            for bone in selected_bones:
                # Create an empty at the location of the bone
                empty = bpy.data.objects.new(f"CopyT_{bone.name}", None)
                empty.location = bone.matrix.to_translation()
                
                # Link the empty object to the current scene collection
                context.collection.objects.link(empty)

                # Add a copy transform constraint to the empty
                constraint = empty.constraints.new(type="COPY_TRANSFORMS")
                constraint.target = armature
                constraint.subtarget = bone.name

                # Add the created empty to the list
                created_empties.append(empty)

            # Store the active object
            original_active_object = context.active_object

            # Switch to object mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Deselect all objects
            bpy.ops.object.select_all(action='DESELECT')

            # Select the created empties
            for empty in created_empties:
                empty.select_set(True)
            context.view_layer.objects.active = created_empties[0]

            # Bake the empties' animation to capture the bone movement
            bpy.ops.nla.bake(
                frame_start=min_frame,
                frame_end=max_frame,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                use_current_action=True,
                bake_types={"OBJECT"}
            )

            # Switch back to the original object and pose mode
            context.view_layer.objects.active = original_active_object
            bpy.ops.object.mode_set(mode='POSE')

            # Add Copy Transforms constraints to the original bones, targeting the empties
            for i, bone in enumerate(selected_bones):
                if i < len(created_empties):
                    constraint = bone.constraints.new(type="COPY_TRANSFORMS")
                    constraint.target = created_empties[i]
            
            # Report success
            self.report({'INFO'}, f"Created and baked {len(created_empties)} empties for transform control.")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating transform controls: {str(e)}")
            return {'CANCELLED'}