import bpy


class AH_offset(bpy.types.Operator):
    """Create manipulator empty system for controlling animated objects"""
    bl_idname = "object.setup_manipulator"
    bl_label = "Setup Manipulator"
    bl_options = {'REGISTER', 'UNDO'}



    def execute(self, context):
        scene = context.scene
        
        # Ensure we have an active object
        if context.active_object is None:
            self.report({'ERROR'}, "No active object selected")
            return {'CANCELLED'}
        
        # Validate frame range
        frame_start = scene.frame_start
        frame_end = scene.frame_end
        if frame_start > frame_end:
            self.report({'ERROR'}, "Invalid frame range")
            return {'CANCELLED'}

        try:
            cursor_location = scene.cursor.location.copy()
            selected_object = context.active_object
            
            # Step 1: Create MANIPULATOR_EMPTY at 3D cursor
            manipulator = bpy.data.objects.new("MANIPULATOR_EMPTY", None)
            manipulator.empty_display_type = 'PLAIN_AXES'
            manipulator.location = cursor_location
            manipulator.rotation_euler = scene.cursor.rotation_euler.copy()  # Align rotation too
            context.collection.objects.link(manipulator)
            
            # Step 2: Parent to animated object
            manipulator.parent = selected_object
            manipulator.matrix_parent_inverse = selected_object.matrix_world.inverted() @ manipulator.matrix_world
            
            # Step 3: Bake MANIPULATOR_EMPTY to preserve animation, then unparent it
            bpy.ops.object.select_all(action='DESELECT')
            manipulator.select_set(True)
            context.view_layer.objects.active = manipulator
            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                clear_parents=True,
                use_current_action=True,
                bake_types={'OBJECT'}
            )
            
            # Step 4: Create OBJECT_EMPTY and match animated object's transform
            object_empty = bpy.data.objects.new("OBJECT_EMPTY", None)
            object_empty.empty_display_type = 'ARROWS'
            context.collection.objects.link(object_empty)
            
            # Copy Transforms to match position and orientation
            ct = object_empty.constraints.new(type='COPY_TRANSFORMS')
            ct.target = selected_object
            
            # Apply constraint to freeze the transform
            context.view_layer.objects.active = object_empty
            bpy.ops.object.select_all(action='DESELECT')
            object_empty.select_set(True)
            bpy.ops.object.visual_transform_apply()
            object_empty.constraints.clear()
            
            # Step 5: Add Copy Transforms to selected object
            copy_trans = selected_object.constraints.new(type='COPY_TRANSFORMS')
            copy_trans.target = object_empty
            copy_trans.name = "AH_OFFSET_CONSTRAINT"
            
            # Step 6: Parent OBJECT_EMPTY to MANIPULATOR_EMPTY
            bpy.ops.object.select_all(action='DESELECT')
            object_empty.select_set(True)
            manipulator.select_set(True)
            context.view_layer.objects.active = manipulator
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

            self.report({'INFO'}, f"Manipulator system created: '{manipulator.name}' and '{object_empty.name}'")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating manipulator system: {str(e)}")
            return {'CANCELLED'}