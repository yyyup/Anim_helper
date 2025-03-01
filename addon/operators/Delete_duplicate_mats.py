import bpy

class AH_MaterialCleanup(bpy.types.Operator):
    """Remove duplicate materials that have a dot in their name and replace them with the original Material"""
    bl_idname = "object.material_cleanup"
    bl_label = "Material CleanUp"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object  # Get the active object

        if not obj or obj.type != 'MESH' or not obj.material_slots:
            self.report({'WARNING'}, "No suitable object selected. Please select a mesh with materials.")
            return {'CANCELLED'}
        
        # First pass: collect all materials that need replacement and their targets
        replacements = {}
        for slot in obj.material_slots:
            if not slot.material:
                continue
                
            if "." in slot.name:
                mat_name = slot.name.rsplit(".", 1)[0]  # Get the material name without dot and numbers
                
                # Check if the original material exists
                if mat_name in bpy.data.materials:
                    replacements[slot.material] = bpy.data.materials[mat_name]
        
        # Second pass: apply all replacements
        for index, slot in enumerate(obj.material_slots):
            if slot.material in replacements:
                # Store the target material
                target_material = replacements[slot.material]
                
                # Set the active material index to this slot
                obj.active_material_index = index
                
                # Replace the material
                slot.material = target_material
        
        # Final pass: remove now-unused materials
        for mat in list(replacements.keys()):
            if mat.users == 0:
                bpy.data.materials.remove(mat)
                
        self.report({'INFO'}, f"Materials cleaned up. Replaced {len(replacements)} materials.")
        return {'FINISHED'}