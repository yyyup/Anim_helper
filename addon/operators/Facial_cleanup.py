import bpy
import re

class AH_RenameAndCleanup(bpy.types.Operator):
    """Rename and organize rig and shapekey actions, then push them to NLA tracks"""
    bl_idname = "object.rename_and_cleanup_actions"
    bl_label = "Rename and Cleanup Actions"
    bl_description = "Rename facial animation actions and push them to the NLA editor"
    bl_options = {'REGISTER', 'UNDO'}

    actions_to_delete = []
    
    # TODO: Set this to your typical body mesh name
    BODY_MESH_BASE_NAME = "CC_Base_Body"  # Change this to your mesh name (e.g., "Head", "Character", "Body")

    def find_body_mesh_in_children(self, rig):
        """
        Find the body mesh among the children of the selected armature.
        Handles naming like: "Body", "Body.001", "Body.002", etc.
        """
        mesh_children = []
        
        # Only look at children of this specific armature
        for child in rig.children:
            if child.type == 'MESH' and self.mesh_name_matches(child.name):
                mesh_children.append(child)
        
        if not mesh_children:
            return None, f"No mesh child named '{self.BODY_MESH_BASE_NAME}' found under armature '{rig.name}'"
        
        # Filter for meshes that have shape keys with animation data
        valid_meshes = []
        for mesh in mesh_children:
            if mesh.data.shape_keys:
                if mesh.data.shape_keys.animation_data and mesh.data.shape_keys.animation_data.action:
                    valid_meshes.append(mesh)
        
        if not valid_meshes:
            mesh_names = [m.name for m in mesh_children]
            return None, f"Found mesh children {mesh_names} but none have animated shape keys"
        
        # Prioritize exact name match, then alphabetical
        valid_meshes.sort(key=lambda x: (
            x.name != self.BODY_MESH_BASE_NAME,  # Exact match first
            x.name  # Then alphabetical
        ))
        
        return valid_meshes[0], None
    
    def mesh_name_matches(self, mesh_name):
        """
        Check if mesh name matches the base pattern (handles .001, .002, etc.)
        Examples: "Body" matches "Body", "Body.001", "Body.002"
        """
        # Exact match
        if mesh_name == self.BODY_MESH_BASE_NAME:
            return True
        
        # Pattern match for numbered duplicates
        pattern = rf"^{re.escape(self.BODY_MESH_BASE_NAME)}\.(\d{{3}})$"
        return bool(re.match(pattern, mesh_name))

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

            # Auto-detect body mesh from rig's children
            body_mesh, error_msg = self.find_body_mesh_in_children(rig)
            if not body_mesh:
                self.report({'ERROR'}, error_msg)
                return {'CANCELLED'}

            # Get the shapekey action
            shapekey_action = body_mesh.data.shape_keys.animation_data.action
            if not shapekey_action:
                self.report({'ERROR'}, f"No active shapekey action found on mesh '{body_mesh.name}'.")
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
                self.report({'INFO'}, f"Found body mesh: '{body_mesh.name}'. {len(self.actions_to_delete)} unnecessary actions found.")
                return context.window_manager.invoke_confirm(self, event=None)
            else:
                self.report({'INFO'}, f"Actions renamed and pushed to NLA using mesh '{body_mesh.name}'. No unnecessary actions to delete.")
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