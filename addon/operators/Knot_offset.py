import bpy
from bpy.types import Operator
from mathutils import Vector

class AH_KnotOffset(Operator):
    """Create empties constrained to selected bone or object with modal placement"""
    bl_idname = "object.create_constrained_empties"
    bl_label = "Knot Offset"
    bl_description = "Create constrained empties with interactive offset positioning"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Variables to store objects and state
    first_empty = None
    second_empty = None
    initial_mouse_x = 0
    initial_mouse_y = 0
    
    # Axis constraint flags
    constrain_x = False
    constrain_y = False
    constrain_z = False
    
    start_location = None
    offset_vector = None
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'ERROR'}, "No active object selected")
            return {'CANCELLED'}
        
        # Handle armatures with pose bones
        if active_obj.type == 'ARMATURE' and context.mode == 'POSE':
            if not context.active_pose_bone:
                self.report({'ERROR'}, "No active pose bone selected")
                return {'CANCELLED'}
            
            # Get the selected bone and its armature
            active_bone = context.active_pose_bone
            armature = active_obj
            
            # Create first empty (the constrained one)
            first_empty = bpy.data.objects.new("BoneConstrained_Empty", None)
            first_empty.empty_display_type = 'SPHERE'
            first_empty.empty_display_size = 0.2
            context.collection.objects.link(first_empty)
            
            # Add Copy Transforms constraint targeting the selected bone
            copy_transform = first_empty.constraints.new('COPY_TRANSFORMS')
            copy_transform.target = armature
            copy_transform.subtarget = active_bone.name
            
            # Calculate world space location for better initial placement
            bone_matrix_world = armature.matrix_world @ active_bone.matrix
            first_empty.matrix_world = bone_matrix_world
            
        # Handle mesh and other object types
        else:
            # Create first empty (the constrained one)
            first_empty = bpy.data.objects.new("ObjectConstrained_Empty", None)
            first_empty.empty_display_type = 'SPHERE'
            first_empty.empty_display_size = 0.2
            context.collection.objects.link(first_empty)
            
            # Add Copy Transforms constraint targeting the selected object
            copy_transform = first_empty.constraints.new('COPY_TRANSFORMS')
            copy_transform.target = active_obj
            
            # Match the object's world transform
            first_empty.matrix_world = active_obj.matrix_world.copy()
        
        # Store reference to the empty
        self.first_empty = first_empty
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        # First create the constrained empty
        exec_result = self.execute(context)
        
        if 'CANCELLED' in exec_result:
            return {'CANCELLED'}
        
        # Remember original mode to restore later
        self.original_mode = context.mode
        
        # Switch to object mode for the modal operation
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create the second empty that will be positioned in modal state
        second_empty = bpy.data.objects.new("Manipulator_Empty", None)
        second_empty.empty_display_type = 'CUBE'
        second_empty.empty_display_size = 0.15
        context.collection.objects.link(second_empty)
        
        # Parent the second empty to the first one, but maintain global orientation
        # First position it at the same location as the first empty
        second_empty.location = self.first_empty.location.copy()
        
        # Use parent_set with keep_transform to maintain global orientation
        bpy.ops.object.select_all(action='DESELECT')
        second_empty.select_set(True)
        self.first_empty.select_set(True)
        context.view_layer.objects.active = self.first_empty
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        
        # Select the second empty for manipulation
        bpy.ops.object.select_all(action='DESELECT')
        second_empty.select_set(True)
        context.view_layer.objects.active = second_empty
        
        # Store the second empty and starting mouse position
        self.second_empty = second_empty
        self.initial_mouse_x = event.mouse_x
        self.initial_mouse_y = event.mouse_y
        
        # Store starting location for constraint operations
        self.start_location = second_empty.location.copy()
        
        # Calculate and store the offset from mouse to object center
        region = context.region
        rv3d = context.region_data
        view_vector = rv3d.view_matrix.inverted().to_3x3()
        self.offset_vector = second_empty.location.copy()
        
        # Set status text to guide the user
        context.workspace.status_text_set(
            "Move the empty. X/Y/Z to constrain axes. LMB: Confirm, RMB/ESC: Cancel"
        )
        
        # Change cursor to indicate move operation
        context.window.cursor_modal_set('HAND')
        
        # Start the modal operator
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        # Handle axis constraint toggles
        if event.type in {'X', 'Y', 'Z'} and event.value == 'PRESS':
            # Toggle constraints like the standard move tool
            if event.type == 'X':
                self.constrain_x = not self.constrain_x
                self.constrain_y = self.constrain_z = False
            elif event.type == 'Y':
                self.constrain_y = not self.constrain_y
                self.constrain_x = self.constrain_z = False
            elif event.type == 'Z':
                self.constrain_z = not self.constrain_z
                self.constrain_x = self.constrain_y = False
            
            # Update status text to show active constraint
            constraint_text = ""
            if self.constrain_x: constraint_text = " (X axis)"
            elif self.constrain_y: constraint_text = " (Y axis)"
            elif self.constrain_z: constraint_text = " (Z axis)"
            
            context.workspace.status_text_set(
                f"Move empty{constraint_text}. X/Y/Z to constrain. LMB: Confirm, RMB/ESC: Cancel"
            )
            
            return {'RUNNING_MODAL'}
        
        # Calculate mouse movement
        delta_x = event.mouse_x - self.initial_mouse_x
        delta_y = event.mouse_y - self.initial_mouse_y
        
        if event.type == 'MOUSEMOVE':
            # Get the current view orientation
            region = context.region
            rv3d = context.region_data
            
            # Calculate total displacement from initial position
            # This makes the object follow the mouse directly rather than using incremental movement
            mouse_delta_x = event.mouse_x - self.initial_mouse_x
            mouse_delta_y = event.mouse_y - self.initial_mouse_y
            
            # Get view vectors
            view_matrix = rv3d.view_matrix.inverted().to_3x3()
            right_vector = view_matrix[0].normalized()
            up_vector = view_matrix[1].normalized()
            
            # Adjust sensitivity based on distance to make movement feel consistent at any zoom level
            distance = rv3d.view_distance if hasattr(rv3d, 'view_distance') else 10.0
            sensitivity = distance * 0.001
            
            # Always start from original position to prevent drift errors
            self.second_empty.location = self.start_location.copy()
            
            # Handle movement based on constraints
            if self.constrain_x:
                # Local X axis only
                self.second_empty.location.x += mouse_delta_x * sensitivity
            elif self.constrain_y:
                # Local Y axis only
                self.second_empty.location.y += mouse_delta_y * sensitivity
            elif self.constrain_z:
                # Local Z axis only 
                self.second_empty.location.z += (mouse_delta_x + mouse_delta_y) * 0.5 * sensitivity
            else:
                # Calculate view-aligned movement vector
                movement = (right_vector * mouse_delta_x + up_vector * mouse_delta_y) * sensitivity
                self.second_empty.location += movement
            
            # Update mouse position for next movement
            self.initial_mouse_x = event.mouse_x
            self.initial_mouse_y = event.mouse_y
            
            # Force redraw for smoother feedback
            context.area.tag_redraw()
        
        # Handle finishing or cancellation
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            # Cancel operation - clean up and remove empties
            self.cleanup(context)
            bpy.data.objects.remove(self.second_empty, do_unlink=True)
            bpy.data.objects.remove(self.first_empty, do_unlink=True)
            self.report({'INFO'}, "Operation cancelled")
            return {'CANCELLED'}
        
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            # Confirm placement - keep empties but exit modal state
            self.cleanup(context)
            self.report({'INFO'}, "Empties created and positioned")
            return {'FINISHED'}
        
        # Continue running modal
        return {'RUNNING_MODAL'}
    
    def cleanup(self, context):
        # Reset UI elements
        context.window.cursor_modal_restore()
        context.workspace.status_text_set(None)
        
        # Restore original mode if we were in pose mode
        if hasattr(self, 'original_mode') and self.original_mode == 'POSE':
            bpy.ops.object.mode_set(mode='POSE')