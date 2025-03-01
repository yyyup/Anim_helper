import bpy

class AH_DuplicateSelectedBonesAction(bpy.types.Operator):
    """Create a new action containing only the animation for selected bones"""
    bl_idname = "pose.duplicate_selected_bones_action"
    bl_label = "Duplicate Action for Selected Bones"
    bl_options = {'REGISTER', 'UNDO'}

    new_action_name: bpy.props.StringProperty(
        name="New Action Name", 
        default="NewAction",
        description="Name for the duplicated action"
    )

    def execute(self, context):
        obj = context.object

        # Ensure the object is an armature in pose mode
        if obj is None or obj.type != 'ARMATURE' or context.mode != 'POSE':
            self.report({'ERROR'}, "Active object must be an armature in Pose Mode")
            return {'CANCELLED'}
        
        # Get the active action
        if not obj.animation_data or not obj.animation_data.action:
            self.report({'ERROR'}, "No active action found on the armature")
            return {'CANCELLED'}
            
        action = obj.animation_data.action
        
        # Get selected bones
        selected_bones = [bone.name for bone in context.selected_pose_bones]
        if not selected_bones:
            self.report({'ERROR'}, "No bones selected")
            return {'CANCELLED'}

        try:
            # Duplicate the action
            new_action = action.copy()
            new_action.name = self.new_action_name

            # Create a list of fcurves to remove (doing this in two passes to avoid
            # issues with removing fcurves while iterating)
            fcurves_to_remove = []
            
            # Filter keyframes for selected bones only
            for fcurve in new_action.fcurves:
                is_selected_bone = False
                if "pose.bones" in fcurve.data_path:
                    for bone_name in selected_bones:
                        if f'pose.bones["{bone_name}"]' in fcurve.data_path:
                            is_selected_bone = True
                            break
                    
                    if not is_selected_bone:
                        fcurves_to_remove.append(fcurve)
            
            # Remove fcurves for unselected bones
            for fcurve in fcurves_to_remove:
                new_action.fcurves.remove(fcurve)

            # Push the new action down into the NLA editor
            track = obj.animation_data.nla_tracks.new()
            track.name = new_action.name
            strip = track.strips.new(name=new_action.name, start=0, action=new_action)

            self.report({'INFO'}, f"Action '{new_action.name}' created with animation for {len(selected_bones)} bones and pushed to NLA")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error duplicating action: {str(e)}")
            return {'CANCELLED'}
            
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)