import bpy

class Anim_H_CenterObjectsXY(bpy.types.Operator):
    bl_idname = "object.center_objects_xy"
    bl_label = "Center Objects in X and Y"
    bl_description = "Center all selected objects to the origin along the X and Y axes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get all selected objects
        selected_objects = bpy.context.selected_objects
        
        for obj in selected_objects:
            # Set the object's X and Y location to 0, keeping Z the same
            obj.location.x = 0
            obj.location.y = 0
        
        self.report({'INFO'}, f"{len(selected_objects)} objects centered to the origin in X and Y axes.")
        return {'FINISHED'}