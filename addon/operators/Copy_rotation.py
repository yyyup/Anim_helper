import bpy

class AH_CopyRotation(bpy.types.Operator):
    """Create empty objects that copy and can reverse the rotation of selected bones or mesh objects"""
    bl_idname = "anim_h.copy_rotation"
    bl_label = "Copy Rotation with Reverse"
    bl_description = "Space switch: Create empties that copy rotation for advanced animation control"
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
    
    def find_armature_frame_range(self, armature, bones, rotation_only=True):
        """Find the animation frame range for bones in an armature"""
        min_frame = float('inf')
        max_frame = float('-inf')
        has_animation = False
        
        # Check for animation data
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            
            # Look for keyframes on the specific bones
            for bone in bones:
                bone_path = f'pose.bones["{bone.name}"]'
                for fcurve in action.fcurves:
                    if bone_path in fcurve.data_path:
                        # For rotation-only check, filter curves
                        if rotation_only and "rotation" not in fcurve.data_path:
                            continue
                            
                        if fcurve.keyframe_points:
                            has_animation = True
                            for keyframe in fcurve.keyframe_points:
                                min_frame = min(min_frame, keyframe.co.x)
                                max_frame = max(max_frame, keyframe.co.x)
        
        # Check NLA strips if no direct action keyframes found
        if not has_animation and armature.animation_data:
            for track in armature.animation_data.nla_tracks:
                for strip in track.strips:
                    has_animation = True
                    min_frame = min(min_frame, strip.frame_start)
                    max_frame = max(max_frame, strip.frame_end)
                    
        # If still no animation found, check for object animation on armature
        if not has_animation and armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            for fcurve in action.fcurves:
                if not 'pose.bones' in fcurve.data_path:
                    if rotation_only and "rotation" not in fcurve.data_path:
                        continue
                        
                    if fcurve.keyframe_points:
                        has_animation = True
                        for keyframe in fcurve.keyframe_points:
                            min_frame = min(min_frame, keyframe.co.x)
                            max_frame = max(max_frame, keyframe.co.x)
        
        if has_animation:
            return int(min_frame), int(max_frame), True
        else:
            return 0, 0, False
            
    def find_object_frame_range(self, obj, rotation_only=True):
        """Recursively find the animation frame range from an object and its parents"""
        min_frame = float('inf')
        max_frame = float('-inf')
        has_animation = False
        
        # Check the object's own animation
        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            for fcurve in action.fcurves:
                if rotation_only and "rotation" not in fcurve.data_path:
                    continue
                    
                if fcurve.keyframe_points:
                    has_animation = True
                    for keyframe in fcurve.keyframe_points:
                        min_frame = min(min_frame, keyframe.co.x)
                        max_frame = max(max_frame, keyframe.co.x)
        
        # If no rotation animation found but rotation_only is True, try again without filter
        if rotation_only and not has_animation and obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            for fcurve in action.fcurves:
                if fcurve.keyframe_points:
                    has_animation = True
                    for keyframe in fcurve.keyframe_points:
                        min_frame = min(min_frame, keyframe.co.x)
                        max_frame = max(max_frame, keyframe.co.x)
        
        # Check NLA strips if no direct action keyframes found
        if not has_animation and obj.animation_data:
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    has_animation = True
                    min_frame = min(min_frame, strip.frame_start)
                    max_frame = max(max_frame, strip.frame_end)
                        
        # If this object has no animation but has a parent, check the parent
        if not has_animation and obj.parent:
            parent_min, parent_max, parent_has_anim = self.find_object_frame_range(obj.parent, rotation_only)
            
            if parent_has_anim:
                min_frame = parent_min
                max_frame = parent_max
                has_animation = True
                
        # If no animation found so far, check for constraints that might have keyframes
        if not has_animation:
            for constraint in obj.constraints:
                if constraint.type in {'FOLLOW_PATH', 'TRACK_TO'} and constraint.target:
                    target_min, target_max, target_has_anim = self.find_object_frame_range(constraint.target, rotation_only)
                    if target_has_anim:
                        min_frame = target_min
                        max_frame = target_max
                        has_animation = True
                        break
        
        if has_animation:
            return int(min_frame), int(max_frame), True
        else:
            return 0, 0, False
            
    def process_bones(self, context):
        """Handle selected pose bones"""
        # Get the selected bones in pose mode
        selected_bones = context.selected_pose_bones
        
        # Check if any bones are selected
        if not selected_bones or len(selected_bones) == 0:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}
        
        # Try to detect frame range from animation
        armature = selected_bones[0].id_data
        min_frame, max_frame, has_animation = self.find_armature_frame_range(armature, selected_bones, True)
        
        # If no animation found, use scene frame range
        if not has_animation:
            min_frame = context.scene.frame_start
            max_frame = context.scene.frame_end
            self.report({'INFO'}, f"No direct animation found. Using scene frame range: {min_frame} to {max_frame}")
        else:
            self.report({'INFO'}, f"Found animation frame range: {min_frame} to {max_frame}")
        
        # Create empties for the selected bones
        created_empties = []
        try:
            # Create an empty for each selected bone
            for bone in selected_bones:
                # Create an empty at the location of the bone
                empty = bpy.data.objects.new(f"CopyRot_{bone.name}", None)
                empty.empty_display_type = 'ARROWS'  # Visual indicator for rotation
                
                # Calculate world space location and rotation
                armature = bone.id_data
                bone_matrix_world = armature.matrix_world @ bone.matrix
                empty.matrix_world = bone_matrix_world
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
        selected_objects = [obj for obj in context.selected_objects if obj.type in {'MESH', 'EMPTY', 'CURVE', 'ARMATURE'}]
        
        if not selected_objects:
            self.report({'WARNING'}, "No valid objects selected.")
            return {'CANCELLED'}
            
        # Find frame range from all selected objects and their parents
        min_frame = float('inf')
        max_frame = float('-inf')
        has_animation = False
        
        for obj in selected_objects:
            obj_min, obj_max, obj_has_anim = self.find_object_frame_range(obj, True)
            
            if obj_has_anim:
                has_animation = True
                min_frame = min(min_frame, obj_min)
                max_frame = max(max_frame, obj_max)
        
        # If no animation is found, use scene frame range
        if not has_animation:
            min_frame = context.scene.frame_start
            max_frame = context.scene.frame_end
            self.report({'INFO'}, f"No direct animation found. Using scene frame range: {min_frame} to {max_frame}")
        else:
            self.report({'INFO'}, f"Found animation frame range: {min_frame} to {max_frame}")
            
        # Create empties for the selected objects
        created_empties = []
        try:
            # Create an empty for each selected object
            for obj in selected_objects:
                # Create an empty at the location of the object
                empty = bpy.data.objects.new(f"CopyRot_{obj.name}", None)
                empty.empty_display_type = 'ARROWS'  # Visual indicator for rotation
                
                # Set the initial transform to match the object's current world transform
                empty.matrix_world = obj.matrix_world.copy()
                empty.rotation_mode = obj.rotation_mode  # Match rotation mode
                
                # Link the empty object to the current scene collection
                context.collection.objects.link(empty)

                # Add a copy rotation constraint to the empty
                constraint = empty.constraints.new(type="COPY_ROTATION")
                constraint.target = obj

                # Add the created empty to the list
                created_empties.append({
                    "empty": empty,
                    "original": obj
                })

            # Store the active object
            original_active_object = context.active_object

            # Deselect all objects
            bpy.ops.object.select_all(action='DESELECT')

            # Select the created empties
            for item in created_empties:
                item["empty"].select_set(True)
            context.view_layer.objects.active = created_empties[0]["empty"]

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
            for item in created_empties:
                constraint = item["original"].constraints.new(type="COPY_ROTATION")
                constraint.target = item["empty"]
            
            # Apply cycling modifier to the empty rotations for reversed animation effect
            for item in created_empties:
                empty = item["empty"]
                if empty.animation_data and empty.animation_data.action:
                    for fcurve in empty.animation_data.action.fcurves:
                        if "rotation" in fcurve.data_path:
                            cycles_mod = fcurve.modifiers.new('CYCLES')
                            fcurve.update()
            
            # Report success
            self.report({'INFO'}, f"Created and baked {len(created_empties)} empties for object rotation control.")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating rotation controls for objects: {str(e)}")
            return {'CANCELLED'}