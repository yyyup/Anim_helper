import bpy

bpy.props.FloatProperty(name= "Factor", default=0.75, min=0, max=1)

class Anim_OP_Decimate(bpy.types.Operator):
    """Decimate baked keys by a ratio of 75%"""
    bl_idname = "anim.decimate_keys_75"
    bl_label = "Decimate Keys"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            # Store the original area type
            original_area_type = context.area.type
            
            # Change the active area to Graph Editor
            context.area.type = 'GRAPH_EDITOR'
            
            # Perform the decimation
            bpy.ops.graph.decimate(mode='RATIO', factor=context.scene.Factor)
            
            # Restore the original area type
            context.area.type = original_area_type
            
            self.report({'INFO'}, "Keys decimated successfully.")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"An error occurred: {e}")
            return {'CANCELLED'}
