import bpy

class AH_RenameAndCleanup(bpy.types.Operator):
    """Rename and organize rig and shapekey actions, then push them to NLA tracks"""
    bl_idname = "object.rename_and_cleanup_actions"
    bl_label = "Rename and Cleanup Actions"
    bl_description = "Rename facial animation actions and push them to the NLA editor"
    bl_options = {'REGISTER', 'UNDO'}

    actions_to_delete = []

    def execute(self, context):
        try:
            rig = context.object

            # Ensure a rig is selected
            if rig is None or rig.type != 'ARMATURE':
                self.report({'ERROR'}, "No rig selected. Please select an armature object and try again.")
                return {'CANCELLED'}

            # Get the active action on the rig
            if not rig.animation_data or not rig.animation_data.action:
                self.report({'ERROR'}, "No active action found on the rig.")
                return {'CANCELLED'}
                
            rig_action = rig.animation_data.action

            # Get specified body mesh
            body_mesh_name = context.scene.fprops.body_mesh_name
            body_mesh = bpy.data.objects.get(body_mesh_name)
            if not body_mesh or body_mesh.type != 'MESH':
                self.report({'ERROR'}, f"Body mesh '{body_mesh_name}' not found or is not a mesh object.")
                return {'CANCELLED'}

            # Check for shapekey animation
            if not body_mesh.data.shape_keys or not body_mesh.data.shape_keys.animation_data:
                self.report({'ERROR'}, "No shapekey animation data found on the body mesh.")
                return {'CANCELLED'}
                
            shapekey_action = body_mesh.data.shape_keys.animation_data.action
            if not shapekey_action:
                self.report({'ERROR'}, "No active shapekey action found on the body mesh.")
                return {'CANCELLED'}

            # Rename the actions
            rig_action.name = context.scene.fprops.rig_action_name
            shapekey_action.name = context.scene.fprops.shapekey_action_name

            # Push rig action to NLA
            rig_nla_track = rig.animation_data.nla_tracks.new()
            rig_nla_track.name = "Rig Action Track"
            rig_nla_track.strips.new(rig_action.name, int(rig_action.frame_range[0]), rig_action)

            # Push shapekey action to NLA
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
                self.report({'INFO'}, "Actions renamed, pushed to NLA. No unnecessary actions to delete.")
                return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error during rename and cleanup: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        if hasattr(self, 'actions_to_delete') and self.actions_to_delete:
            message = "The following actions will be deleted:\n"
            for action in self.actions_to_delete:
                message += f"- {action.name}\n"
            self.report({'INFO'}, message)
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.label(text="The following actions will be deleted:")
        for action in self.actions_to_delete:
            layout.label(text=f"- {action.name}")