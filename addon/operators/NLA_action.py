import bpy

class Anim_H_NLA(bpy.types.Operator):
    """Duplicate Action for Selected Bones"""
    bl_idname = "pose.duplicate_selected_bones_action"
    bl_label = "Duplicate Action for Selected Bones"
    bl_options = {'REGISTER', 'UNDO'}

    new_action_name: bpy.props.StringProperty(name="New Action Name", default="NewAction")

    def execute(self, context):
        obj = context.object

        # Ensure the object is an armature in pose mode
        if obj is None or obj.type != 'ARMATURE' or context.mode != 'POSE':
            self.report({'ERROR'}, "Active object must be an armature in Pose Mode")
            return {'CANCELLED'}
        
        # Get the active action
        action = obj.animation_data.action
        if action is None:
            self.report({'ERROR'}, "No active action found on the armature")
            return {'CANCELLED'}
        
        # Get selected bones
        selected_bones = [bone.name for bone in context.selected_pose_bones]
        if not selected_bones:
            self.report({'ERROR'}, "No bones selected")
            return {'CANCELLED'}

        # Duplicate the action
        new_action = action.copy()
        new_action.name = self.new_action_name

        # Filter keyframes for selected bones only
        for fcurve in new_action.fcurves:
            if "pose.bones" in fcurve.data_path:
                bone_name = fcurve.data_path.split('"')[1]
                if bone_name not in selected_bones:
                    # Remove F-Curve for unselected bones
                    new_action.fcurves.remove(fcurve)

        # Push the new action down into the NLA editor
        if obj.animation_data.nla_tracks:
            track = obj.animation_data.nla_tracks.new()
        else:
            track = obj.animation_data.nla_tracks.new()
        track.name = new_action.name
        strip = track.strips.new(name=new_action.name, start=0, action=new_action)

        self.report({'INFO'}, f"Action '{new_action.name}' created and pushed to NLA")
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    


