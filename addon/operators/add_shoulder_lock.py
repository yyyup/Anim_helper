import bpy

class AH_ShoulderLock(bpy.types.Operator):
    """Creates rotation-locked controls for shoulder bones in FK chains"""
    bl_idname = "shoulder.lock"
    bl_label = "Add Shoulder Lock"
    bl_description = "Create empties that lock shoulder rotation for FK chain"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the selected bones in pose mode
        selected_bones = context.selected_pose_bones
        
        # Check if selected_bones is None or if any bones are selected
        if not selected_bones or len(selected_bones) == 0:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}
        
        try:
            # Get armature
            armature = context.active_object
            
            # Create an empty list to store the created empties
            created_empties = []

            # Loop through each selected bone
            for bone in selected_bones: 
                # Create an empty at the location of the bone
                empty = bpy.data.objects.new(f"ShoulderLock_{bone.name}", None)
                empty.location = bone.matrix.to_translation()
                
                # Link the empty object to the current scene collection
                context.collection.objects.link(empty)

                # Add a rotation constraint to the empty
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

            # Select the created empties and set the first one as the active object
            for empty in created_empties:
                empty.select_set(True)
            context.view_layer.objects.active = created_empties[0]

            # Get frame range from scene
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end

            # Bake the action with the specified options
            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                use_current_action=True,
                bake_types={"OBJECT"}
            )

            # Set the original active object back and switch back to pose mode
            context.view_layer.objects.active = original_active_object
            bpy.ops.object.mode_set(mode='POSE')

            # Add rotation constraints to the original selected bones
            for i, bone in enumerate(selected_bones):
                # Get the corresponding baked empty
                empty = created_empties[i]

                # Add a rotation constraint to the bone
                constraint = bone.constraints.new(type="COPY_ROTATION")
                constraint.target = empty
                
            # Apply cycles modifier to the empties and offset their keyframes by 2 frames
            for empty in created_empties:
                if not empty.animation_data or not empty.animation_data.action:
                    continue
                    
                action = empty.animation_data.action
                # Apply cycles modifier and offset to rotation curves
                for fcurve in action.fcurves:
                    if fcurve.data_path == "rotation_euler":
                        # Add cycles modifier
                        cycles_mod = fcurve.modifiers.new('CYCLES')
                        
                        # Offset keyframes by 2 frames
                        for keyframe in fcurve.keyframe_points:
                            keyframe.co.x += 2
                        fcurve.update()
            
            self.report({'INFO'}, f"Created shoulder lock controls for {len(created_empties)} bones with 2-frame offset.")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating shoulder lock: {str(e)}")
            return {'CANCELLED'}