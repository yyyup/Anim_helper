import bpy

class AH_CopyRotation(bpy.types.Operator):
    """Create empty objects that copy and can reverse the rotation of selected bones or mesh objects"""
    bl_idname = "anim_h.copy_rotation"
    bl_label = "Copy Rotation with Reverse"
    bl_description = "Create empties that copy rotation from bones or mesh objects for advanced animation control"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Check what's selected and active
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'WARNING'}, "No active object selected.")
            return {'CANCELLED'}
            
        # Handle armatures with pose bones
        if active_obj.type == 'ARMATURE' and context.mode == 'POSE':
            return self.process_bones(context)
        # Handle mesh objects
        elif context.selected_objects:
            return self.process_mesh_objects(context)
        else:
            self.report({'WARNING'}, "Please select an armature in pose mode or mesh objects.")
            return {'CANCELLED'}
            
    def process_bones(self, context):
        """Handle selected pose bones"""
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
                if bone_path in fcurve.data_path and "rotation" in fcurve.data_path and fcurve.keyframe_points:
                    for keyframe in fcurve.keyframe_points:
                        min_frame = min(min_frame, keyframe.co.x)
                        max_frame = max(max_frame, keyframe.co.x)

        if min_frame == float('inf') or max_frame == float('-inf'):
            self.report({'WARNING'}, "No rotation keyframes found in the selected bones.")
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
                empty = bpy.data.objects.new(f"CopyRot_{bone.name}", None)
                empty.empty_display_type = 'ARROWS'  # Visual indicator for rotation
                empty.location = bone.matrix.to_translation()
                empty.rotation_mode = bone.rotation_mode  # Match rotation mode
                
                # Link the empty object to the current scene collection
                context.collection.objects.link(empty)

                # Add a copy rotation constraint to the empty
                constraint = empty.constraints.new(type="COPY_ROTATION")
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

            # Bake the empties' animation to capture the bone rotation
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

            # Add Copy Rotation constraints to the original bones, targeting the empties
            for i, bone in enumerate(selected_bones):
                if i < len(created_empties):
                    constraint = bone.constraints.new(type="COPY_ROTATION")
                    constraint.target = created_empties[i]
            
            # Report success
            self.report({'INFO'}, f"Created and baked {len(created_empties)} empties for bone rotation control.")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating rotation controls for bones: {str(e)}")
            return {'CANCELLED'}
            
    def process_mesh_objects(self, context):
        """Handle selected mesh objects"""
        selected_objects = [obj for obj in context.selected_objects if obj.type in {'MESH', 'EMPTY', 'CURVE'}]
        
        if not selected_objects:
            self.report({'WARNING'}, "No valid objects selected.")
            return {'CANCELLED'}
            
        # Find frame range from all selected objects
        min_frame = float('inf')
        max_frame = float('-inf')
        
        has_animation = False
        
        for obj in selected_objects:
            if obj.animation_data and obj.animation_data.action:
                has_animation = True
                action = obj.animation_data.action
                for fcurve in action.fcurves:
                    if "rotation" in fcurve.data_path and fcurve.keyframe_points:
                        for keyframe in fcurve.keyframe_points:
                            min_frame = min(min_frame, keyframe.co.x)
                            max_frame = max(max_frame, keyframe.co.x)
        
        # If no animation is found, use scene frame range
        if not has_animation or min_frame == float('inf') or max_frame == float('-inf'):
            min_frame = context.scene.frame_start
            max_frame = context.scene.frame_end
            
        # Create empties for the selected objects
        created_empties = []
        try:
            # Create an empty for each selected object
            for obj in selected_objects:
                # Create an empty at the location of the object
                empty = bpy.data.objects.new(f"CopyRot_{obj.name}", None)
                empty.empty_display_type = 'ARROWS'  # Visual indicator for rotation
                empty.location = obj.location
                empty.rotation_euler = obj.rotation_euler
                empty.rotation_mode = obj.rotation_mode  # Match rotation mode
                
                # Link the empty object to the current scene collection
                context.collection.objects.link(empty)

                # Add a copy rotation constraint to the empty
                constraint = empty.constraints.new(type="COPY_ROTATION")
                constraint.target = obj

                # Add the created empty to the list
                created_empties.append(empty)

            # Store the active object
            original_active_object = context.active_object

            # Deselect all objects
            bpy.ops.object.select_all(action='DESELECT')

            # Select the created empties
            for empty in created_empties:
                empty.select_set(True)
            context.view_layer.objects.active = created_empties[0]

            # Bake the empties' animation
            bpy.ops.nla.bake(
                frame_start=min_frame,
                frame_end=max_frame,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                use_current_action=True,
                bake_types={"OBJECT"}
            )

            # Restore original selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            context.view_layer.objects.active = original_active_object

            # Add Copy Rotation constraints to the original objects, targeting the empties
            for i, obj in enumerate(selected_objects):
                if i < len(created_empties):
                    constraint = obj.constraints.new(type="COPY_ROTATION")
                    constraint.target = created_empties[i]
            
            # Apply cycling modifier to the empty rotations for reversed animation effect
            for empty in created_empties:
                if empty.animation_data and empty.animation_data.action:
                    for fcurve in empty.animation_data.action.fcurves:
                        if "rotation" in fcurve.data_path:
                            cycles_mod = fcurve.modifiers.new('CYCLES')
                            # Optional: Offset keyframes for delayed effect
                            # for keyframe in fcurve.keyframe_points:
                            #     keyframe.co.x += 2
                            fcurve.update()
            
            # Report success
            self.report({'INFO'}, f"Created and baked {len(created_empties)} empties for object rotation control.")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating rotation controls for objects: {str(e)}")
            return {'CANCELLED'}