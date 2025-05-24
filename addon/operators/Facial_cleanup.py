import bpy
import re

class AH_RenameAndCleanup(bpy.types.Operator):
    """Rename and organize rig and shapekey actions, then push them to NLA tracks"""
    bl_idname = "object.rename_and_cleanup_actions"
    bl_label = "Rename and Cleanup Actions"
    bl_description = "Rename facial animation actions and push them to the NLA editor"
    bl_options = {'REGISTER', 'UNDO'}

    actions_to_delete = []
    
    # Body mesh name for Character Creator
    BODY_MESH_BASE_NAME = "CC_Base_Body"
    
    # Facial bones to KEEP (preserve keyframes)
    KEEP_BONES = {
        "brow.T.L.001", "brow.T.L.002", "brow.T.L.003", "brow.T.R.001", "brow.T.R.002", "brow.T.R.003",
        "cheek.B.L.001", "cheek.B.R.001", "chin", "lid.B.L.002", "lid.B.R.002", "lid.T.L.002", "lid.T.R.002",
        "lip.B", "lip.B.L.001", "lip.B.R.001", "lip.T", "lip.T.L.001", "lip.T.R.001", "lips.L", "lips.R",
        "nose.002", "nose.L.001", "nose.R.001", "ear.L", "ear.R", "eye.L", "eye.R", "eyes",
        "jaw_master", "master_eye.L", "master_eye.R", "nose_master", "teeth.B", "teeth.T", "tongue_master",
        "brow.B.L", "brow.B.L.001", "brow.B.L.002", "brow.B.L.003", "brow.B.L.004",
        "brow.B.R", "brow.B.R.001", "brow.B.R.002", "brow.B.R.003", "brow.B.R.004",
        "brow.T.L", "brow.T.R", "cheek.T.L.001", "cheek.T.R.001", "chin.001", "chin.002", "chin.L", "chin.R",
        "ear.L.002", "ear.L.003", "ear.L.004", "ear.R.002", "ear.R.003", "ear.R.004",
        "jaw", "jaw.L", "jaw.L.001", "jaw.R", "jaw.R.001",
        "lid.B.L", "lid.B.L.001", "lid.B.L.003", "lid.B.R", "lid.B.R.001", "lid.B.R.003",
        "lid.T.L", "lid.T.L.001", "lid.T.L.003", "lid.T.R", "lid.T.R.001", "lid.T.R.003",
        "nose", "nose.001", "nose.003", "nose.004", "nose.005", "nose.L", "nose.R",
        "tongue", "tongue.001", "tongue.002", "tongue.003", "head"
    }
    
    # Body bones to DELETE (remove keyframes)  
    DELETE_BONES = {
        "root", "VIS_upper_arm_ik_pole.L", "hand_ik.L", "upper_arm_ik.L", "upper_arm_ik_target.L", "upper_arm_parent.L",
        "VIS_upper_arm_ik_pole.R", "hand_ik.R", "upper_arm_ik.R", "upper_arm_ik_target.R", "upper_arm_parent.R",
        "VIS_thigh_ik_pole.L", "foot_heel_ik.L", "foot_ik.L", "foot_spin_ik.L", "thigh_ik.L", "thigh_ik_target.L",
        "thigh_parent.L", "toe_ik.L", "VIS_thigh_ik_pole.R", "foot_heel_ik.R", "foot_ik.R", "foot_spin_ik.R",
        "thigh_ik.R", "thigh_ik_target.R", "thigh_parent.R", "toe_ik.R", "breast.L", "breast.R",
        "chest", "hips", "neck", "shoulder.L", "shoulder.R", "torso",
        "spine_fk", "spine_fk.001", "spine_fk.002", "spine_fk.003",
        "tweak_spine", "tweak_spine.001", "tweak_spine.002", "tweak_spine.003", "tweak_spine.004", "tweak_spine.005",
        "foot_tweak.L", "shin_tweak.L", "shin_tweak.L.001", "thigh_tweak.L", "thigh_tweak.L.001",
        "foot_tweak.R", "shin_tweak.R", "shin_tweak.R.001", "thigh_tweak.R", "thigh_tweak.R.001",
        "foot_fk.L", "shin_fk.L", "thigh_fk.L", "toe_fk.L", "foot_fk.R", "shin_fk.R", "thigh_fk.R", "toe_fk.R",
        "forearm_tweak.L", "forearm_tweak.L.001", "hand_tweak.L", "upper_arm_tweak.L", "upper_arm_tweak.L.001",
        "forearm_fk.L", "hand_fk.L", "upper_arm_fk.L", "forearm_tweak.R", "forearm_tweak.R.001", "hand_tweak.R",
        "upper_arm_tweak.R", "upper_arm_tweak.R.001", "forearm_fk.R", "hand_fk.R", "upper_arm_fk.R",
        "f_index.01_master.L", "f_index.01_master.R", "f_middle.01_master.L", "f_middle.01_master.R",
        "f_pinky.01_master.L", "f_pinky.01_master.R", "f_ring.01_master.L", "f_ring.01_master.R",
        "palm.L", "palm.R", "thumb.01_master.L", "thumb.01_master.R"
    }

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
    
    def filter_rig_action_bones(self, rig_action):
        """
        KEEP only facial bones, DELETE everything else.
        This ensures only facial animation is preserved.
        """
        if not rig_action or not rig_action.fcurves:
            return 0
        
        fcurves_to_remove = []
        kept_bones = set()
        removed_bones = set()
        
        # Scan all F-curves - ONLY keep facial bones, remove everything else
        for fcurve in rig_action.fcurves:
            # Extract bone name from data path (e.g., 'pose.bones["jaw"].location' -> 'jaw')
            bone_name = self.extract_bone_name_from_fcurve(fcurve.data_path)
            
            if bone_name:
                if bone_name in self.KEEP_BONES:
                    # This is a facial bone - KEEP it
                    kept_bones.add(bone_name)
                else:
                    # This is NOT a facial bone - DELETE it (body, fingers, etc.)
                    fcurves_to_remove.append(fcurve)
                    removed_bones.add(bone_name)
        
        # Remove all non-facial F-curves
        for fcurve in fcurves_to_remove:
            rig_action.fcurves.remove(fcurve)
        
        print(f"Facial bone filtering: Kept {len(kept_bones)} facial bones, removed {len(removed_bones)} other bones")
        print(f"Kept bones: {sorted(kept_bones)}")
        print(f"Removed bones: {sorted(removed_bones)}")
        return len(fcurves_to_remove)
    
    def extract_bone_name_from_fcurve(self, data_path):
        """
        Extract bone name from F-curve data path.
        Examples: 
        'pose.bones["jaw"].location' -> 'jaw'
        'pose.bones["upper_arm_fk.L"].rotation_euler' -> 'upper_arm_fk.L'
        """
        # Pattern to match pose.bones["bone_name"]
        pattern = r'pose\.bones\["([^"]+)"\]'
        match = re.search(pattern, data_path)
        return match.group(1) if match else None

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

            # Filter rig action: Remove body bone keyframes, keep facial bone keyframes
            removed_fcurves = self.filter_rig_action_bones(rig_action)

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
                self.report({'INFO'}, f"Found '{body_mesh.name}'. Filtered {removed_fcurves} body bone F-curves. {len(self.actions_to_delete)} actions to delete.")
                return context.window_manager.invoke_confirm(self, event=None)
            else:
                self.report({'INFO'}, f"Success! Used '{body_mesh.name}', filtered {removed_fcurves} body bone F-curves. Actions organized to NLA.")
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