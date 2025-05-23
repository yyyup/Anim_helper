import bpy

def adjust_empty_display_size(context, delta):
    for obj in context.selected_objects:
        if obj.type == 'EMPTY':
            current_size = obj.empty_display_size
            new_size = max(0.1, current_size + delta)  # prevent going below 1
            obj.empty_display_size = float(new_size)

class AH_OT_EmptySizeGrow(bpy.types.Operator):
    bl_idname = "ah.empty_size_grow"
    bl_label = "Grow Empty"
    bl_description = "Increase display size of selected empties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        adjust_empty_display_size(context, 0.5)
        return {'FINISHED'}

class AH_OT_EmptySizeShrink(bpy.types.Operator):
    bl_idname = "ah.empty_size_shrink"
    bl_label = "Shrink Empty"
    bl_description = "Decrease display size of selected empties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        adjust_empty_display_size(context, -0.5)
        return {'FINISHED'}

