import bpy


class AH_offset_cleanup(bpy.types.Operator):
    """Clean up manipulator empty system by removing empties and constraint"""
    bl_idname = "object.cleanup_manipulator"
    bl_label = "Cleanup Manipulator"
    bl_description = "Remove helper empties and related constraints"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True  # Always allow this operator to run

    def execute(self, context):
        print("AH_offset_cleanup: Starting cleanup...")  # Debug print
        try:
            objects_removed = 0
            constraints_removed = 0
            
            # Remove empties by name (including .001, .002, etc.)
            objects_to_remove = []
            for obj in bpy.data.objects:
                if obj.name.startswith("MANIPULATOR_EMPTY") or obj.name.startswith("OBJECT_EMPTY"):
                    objects_to_remove.append(obj)
            
            for obj in objects_to_remove:
                print(f"Removing object: {obj.name}")  # Debug print
                bpy.data.objects.remove(obj, do_unlink=True)
                objects_removed += 1
            
            # Remove constraints from active object only
            if context.active_object:
                constraints_to_remove = []
                for constraint in context.active_object.constraints:
                    if constraint.name.startswith("AH_OFFSET_CONSTRAINT"):
                        constraints_to_remove.append(constraint)
                
                for constraint in constraints_to_remove:
                    print(f"Removing constraint: {constraint.name}")  # Debug print
                    context.active_object.constraints.remove(constraint)
                    constraints_removed += 1

            if objects_removed > 0 or constraints_removed > 0:
                self.report({'INFO'}, f"Cleanup complete: {objects_removed} empties and {constraints_removed} constraints removed")
            else:
                self.report({'INFO'}, "No manipulator system found to clean up")
            
            print("AH_offset_cleanup: Finished successfully")  # Debug print
            return {'FINISHED'}
            
        except Exception as e:
            print(f"AH_offset_cleanup: Error - {str(e)}")  # Debug print
            self.report({'ERROR'}, f"Error during cleanup: {str(e)}")
            return {'CANCELLED'}