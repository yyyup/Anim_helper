import bpy


class AH_Facialprops(bpy.types.PropertyGroup):
    rig_action_name: bpy.props.StringProperty(
        name="Rig Action Name",
        default="XXX_RA_Speech_01"
    )
    shapekey_action_name: bpy.props.StringProperty(
        name="Shapekey Action Name",
        default="XXX_SA_Speech_01"
    )
    body_mesh_name: bpy.props.StringProperty(
        name="Body Mesh Name",
        default=""
    )




class AH_RenameAndCleanup(bpy.types.Operator):
    bl_idname = "object.rename_and_cleanup_actions"
    bl_label = "Rename and Cleanup Actions"

    actions_to_delete = []

    def execute(self, context):
        rig = context.object

        # Ensure a rig is selected
        if rig is None or rig.type != 'ARMATURE':
            self.report({'ERROR'}, "No rig selected. Please select an armature object and try again.")
            return {'CANCELLED'}

        # Get the active action on the rig
        rig_action = rig.animation_data.action if rig.animation_data else None
        if not rig_action:
            self.report({'ERROR'}, "No active action found on the rig.")
            return {'CANCELLED'}

        # Get specified body mesh
        body_mesh_name = context.scene.fprops.body_mesh_name
        body_mesh = bpy.data.objects.get(body_mesh_name)
        if not body_mesh or body_mesh.type != 'MESH':
            self.report({'ERROR'}, "Specified body mesh not found or invalid.")
            return {'CANCELLED'}

        # Check for shapekey animation by inspecting fcurves
        shapekey_action = None
        if body_mesh.data.shape_keys and body_mesh.data.shape_keys.animation_data:
            shapekey_action = body_mesh.data.shape_keys.animation_data.action

        if not shapekey_action:
            self.report({'ERROR'}, "No active shapekey action found on the body mesh.")
            return {'CANCELLED'}

        # Rename the actions
        rig_action.name = context.scene.fprops.rig_action_name
        shapekey_action.name = context.scene.fprops.shapekey_action_name

        # Push actions to NLA
        # Rig action
        rig_nla_track = rig.animation_data.nla_tracks.new()
        rig_nla_track.name = "Rig Action Track"
        rig_nla_track.strips.new(rig_action.name, int(rig_action.frame_range[0]), rig_action)

        # Shapekey action
        if body_mesh.data.shape_keys.animation_data is None:
            body_mesh.data.shape_keys.animation_data_create()
        shapekey_nla_track = body_mesh.data.shape_keys.animation_data.nla_tracks.new()
        shapekey_nla_track.name = "Shapekey Action Track"
        shapekey_nla_track.strips.new(shapekey_action.name, int(shapekey_action.frame_range[0]), shapekey_action)

        # Clear the active actions
        rig.animation_data.action = None
        body_mesh.data.shape_keys.animation_data.action = None

        # Identify unnecessary actions based on the selected rig
        rig_name_keyword = rig.name
        self.actions_to_delete = [
            action for action in bpy.data.actions 
            if rig_name_keyword in action.name and action != rig_action and action != shapekey_action
        ]

        if self.actions_to_delete:
            self.report({'INFO'}, f"{len(self.actions_to_delete)} unnecessary actions found.")
            return context.window_manager.invoke_confirm(self, event=None)
        else:
            self.report({'INFO'}, "No unnecessary actions to delete.")

        self.report({'INFO'}, "Actions renamed, pushed to NLA, and cleaned up.")
        return {'FINISHED'}

    def invoke(self, context, event):
        message = "The following actions will be deleted:\n"
        for action in self.actions_to_delete:
            message += f"- {action.name}\n"
        self.report({'INFO'}, message)
        return context.window_manager.invoke_confirm(self, event)

    def confirm(self, context):
        for action in self.actions_to_delete:
            bpy.data.actions.remove(action)
        self.report({'INFO'}, f"Deleted {len(self.actions_to_delete)} unnecessary actions.")
        return {'FINISHED'}