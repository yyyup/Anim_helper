import bpy

class AH_DeleteActionsProperties(bpy.types.PropertyGroup):
    keyword: bpy.props.StringProperty(
        name="Keyword",
        description="Keyword to search for in action names",
        default=""
    )


class AH_DeleteActions(bpy.types.Operator):
    """Operator to delete actions by keyword"""
    bl_idname = "action.delete_by_keyword"
    bl_label = "Delete Actions by Keyword"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.actions)

    def execute(self, context):
        keyword = context.scene.Dprops.keyword
        if not keyword:
            self.report({'WARNING'}, "Keyword cannot be empty")
            return {'CANCELLED'}

        actions = bpy.data.actions
        actions_to_delete = [action for action in actions if keyword in action.name]

        if not actions_to_delete:
            self.report({'INFO'}, f"No actions found with keyword: {keyword}")
            return {'CANCELLED'}

        for action in actions_to_delete:
            bpy.data.actions.remove(action)

        self.report({'INFO'}, f"Deleted {len(actions_to_delete)} action(s) with keyword: {keyword}")
        return {'FINISHED'}
