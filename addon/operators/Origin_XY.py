import bpy

class AH_CenterObjectsXY(bpy.types.Operator):
    """Center selected objects to the origin in the X and Y axes, maintaining Z position"""
    bl_idname = "object.center_objects_xy"
    bl_label = "Center Objects in X and Y"
    bl_description = "Center all selected objects to the origin along the X and Y axes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get all selected objects
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}
        
        centered_count = 0
        
        for obj in selected_objects:
            try:
                # Store original Z position
                original_z = obj.location.z
                
                # Set the object's X and Y location to 0
                obj.location.x = 0
                obj.location.y = 0
                
                # Ensure Z position is maintained (in case of precision issues)
                obj.location.z = original_z
                
                centered_count += 1
                
            except Exception as e:
                self.report({'WARNING'}, f"Could not center {obj.name}: {str(e)}")
                continue
        
        if centered_count > 0:
            self.report({'INFO'}, f"{centered_count} objects centered to the origin in X and Y axes.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No objects were centered.")
            return {'CANCELLED'}