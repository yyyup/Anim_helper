import bpy

class AH_DecimateKeys(bpy.types.Operator):
    """Decimate keyframes to reduce animation complexity while preserving motion"""
    bl_idname = "anim.decimate_keys"
    bl_label = "Decimate Keyframes"
    bl_description = "Reduce the number of keyframes in the animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        original_area_type = None
        original_area = None
        factor = context.scene.Factor
        
        try:
            # Find a 3D view area to work with
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    original_area = area
                    original_area_type = area.type
                    area.type = 'GRAPH_EDITOR'
                    break
            
            # If no 3D View found, try to use the current area
            if original_area is None:
                original_area = context.area
                original_area_type = original_area.type
                original_area.type = 'GRAPH_EDITOR'
            
            # Perform the decimation
            bpy.ops.graph.decimate(mode='RATIO', factor=factor)
            
            self.report({'INFO'}, f"Keys decimated successfully. Keeping {factor*100:.1f}% of keyframes.")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to decimate keyframes: {str(e)}")
            return {'CANCELLED'}
        
        finally:
            # Restore the original area type
            if original_area and original_area_type:
                original_area.type = original_area_type