import bpy

class SIMPLE_AH_MaterialCleanUp(bpy.types.Operator):
    """Remove duplicate materials that have a dot in their name and replace them with the original Material"""
    bl_idname = "object.material_cleanup"
    bl_label = "Material CleanUp"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object  # Get the active object

        if obj and obj.type == 'MESH' and obj.material_slots:
            for index in range(len(obj.material_slots)):  # Iterate through each material slot
                obj.active_material_index = index  # Set the active material index
                
                # Check if there's a dot in the material name
                if "." in obj.material_slots[index].name:
                    mat_name = obj.material_slots[index].name.rsplit(".", 1)[0]  # Get the material name without dot and the following numbers
                    
                    # Remove the material with the dot in the name
                    bpy.data.materials.remove(obj.material_slots[index].material)
                    
                    # Assign the cleaned material name to the object
                    if mat_name in bpy.data.materials:
                        obj.material_slots[index].material = bpy.data.materials[mat_name]
                        
            self.report({'INFO'}, "Materials cleaned up.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No suitable object selected.")
            return {'CANCELLED'}
