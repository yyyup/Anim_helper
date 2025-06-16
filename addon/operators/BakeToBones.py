import bpy

class AH_BakeToBones(bpy.types.Operator):
    """Bake animation data to the selected bones of the active armature, overwriting the existing action."""
    bl_idname = "anim_h.bake_to_bones"
    bl_label = "Bake Animation to Selected Bones"
    bl_description = "Bake the combined animation (including NLA layers) to the selected bones, overwriting the existing action"
    bl_options = {'REGISTER', 'UNDO'}

    clear_nla_stack: bpy.props.BoolProperty(
        name="Clear NLA Stack",
        description="Clear the NLA stack after baking (may require manual update in Animation Layers)",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'ARMATURE' and 
                context.mode == 'POSE')

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE' or context.mode != 'POSE':
            self.report({'ERROR'}, "Active object must be an armature in Pose mode.")
            return {'CANCELLED'}

        # Check for selected bones
        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "No bones selected. Please select at least one bone to bake.")
            return {'CANCELLED'}

        # Find the frame range for baking
        min_frame, max_frame, has_animation = self.find_armature_frame_range(armature)
        if not has_animation:
            min_frame = context.scene.frame_start
            max_frame = context.scene.frame_end
            self.report({'INFO'}, f"No animation found. Using scene frame range: {min_frame} to {max_frame}")
        else:
            self.report({'INFO'}, f"Found animation frame range: {min_frame} to {max_frame}")

        # Bake the animation to the selected bones
        try:
            self.bake_to_bones(context, armature, selected_bones, min_frame, max_frame)
            self.report({'INFO'}, f"Successfully baked animation to {len(selected_bones)} selected bones.")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to bake animation to bones: {str(e)}")
            return {'CANCELLED'}

    def find_armature_frame_range(self, armature):
        """Find the animation frame range for the armature, considering the full NLA stack."""
        min_frame = float('inf')
        max_frame = float('-inf')
        has_animation = False
        
        # Check for direct action keyframes on bones
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            for fcurve in action.fcurves:
                if 'pose.bones' in fcurve.data_path and fcurve.keyframe_points:
                    has_animation = True
                    for keyframe in fcurve.keyframe_points:
                        min_frame = min(min_frame, keyframe.co.x)
                        max_frame = max(max_frame, keyframe.co.x)
        
        # Check NLA strips
        if armature.animation_data and armature.animation_data.nla_tracks:
            for track in armature.animation_data.nla_tracks:
                for strip in track.strips:
                    has_animation = True
                    min_frame = min(min_frame, strip.frame_start)
                    max_frame = max(max_frame, strip.frame_end)
                    
        # Check for object animation on the armature
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            for fcurve in action.fcurves:
                if 'pose.bones' not in fcurve.data_path and fcurve.keyframe_points:
                    has_animation = True
                    for keyframe in fcurve.keyframe_points:
                        min_frame = min(min_frame, keyframe.co.x)
                        max_frame = max(max_frame, keyframe.co.x)
        
        if has_animation:
            return int(min_frame), int(max_frame), True
        return 0, 0, False

    def exit_nla_tweak_mode(self, context, armature):
        """Safely exit NLA tweak mode if active, compatible across Blender versions."""
        if not armature.animation_data or not armature.animation_data.nla_tracks:
            return

        try:
            if hasattr(armature.animation_data, 'is_tweakmode') and armature.animation_data.is_tweakmode:
                context.view_layer.objects.active = armature
                bpy.ops.nla.tweakmode_exit()
        except AttributeError:
            for track in armature.animation_data.nla_tracks:
                if track.is_solo or track.mute:
                    continue
                for strip in track.strips:
                    if strip.active:
                        context.view_layer.objects.active = armature
                        bpy.ops.nla.tweakmode_enter()
                        bpy.ops.nla.tweakmode_exit()
                        break
                break

    def bake_to_bones(self, context, armature, selected_bones, frame_start, frame_end):
        """Bake the full NLA stack animation to the selected bones, overwriting the existing action."""
        if not armature.animation_data:
            armature.animation_data_create()

        # Store the existing action (if any) to merge with the new baked keyframes
        existing_action = armature.animation_data.action
        if not existing_action:
            existing_action = bpy.data.actions.new(name=f"{armature.name}_BakedAction")

        # Create a temporary action for baking
        temp_action = bpy.data.actions.new(name="TempBakeAction")
        
        # Store the original mode and switch to Object Mode for selection
        original_mode = context.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all objects using direct property access
        for obj in context.scene.objects:
            obj.select_set(False)

        # Select the armature and set it as active
        armature.select_set(True)
        context.view_layer.objects.active = armature

        # Switch back to Pose Mode for baking
        bpy.ops.object.mode_set(mode='POSE')

        # Exit tweak mode if active
        self.exit_nla_tweak_mode(context, armature)

        # Mute all NLA tracks to isolate the baking
        nla_tracks = armature.animation_data.nla_tracks
        track_mute_states = {}
        if nla_tracks:
            for track in nla_tracks:
                track_mute_states[track] = track.mute
                track.mute = True

        try:
            # Unmute NLA tracks to evaluate the full stack during baking
            if nla_tracks:
                for track in nla_tracks:
                    track.mute = track_mute_states[track]

            # Temporarily assign the temp action
            original_action = armature.animation_data.action
            try:
                armature.animation_data.action = temp_action
            except Exception as e:
                self.report({'WARNING'}, f"Failed to assign temp action: {str(e)}. Proceeding with baking.")
                temp_action = None

            # Bake the animation to all bones
            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=False,
                bake_types={'POSE'}
            )

            # Get the baked action (it might be temp_action or a new one created by nla.bake)
            baked_action = armature.animation_data.action
            if not baked_action:
                raise Exception("Failed to create a new action during baking.")

            # Filter keyframes for selected bones in the baked action
            selected_bone_names = {bone.name for bone in selected_bones}
            for fcurve in list(baked_action.fcurves):
                if 'pose.bones' in fcurve.data_path:
                    bone_name = fcurve.data_path.split('"')[1]
                    if bone_name not in selected_bone_names:
                        baked_action.fcurves.remove(fcurve)

            # Merge the baked keyframes into the existing action
            for fcurve in list(baked_action.fcurves):
                # Find or create a matching fcurve in the existing action
                existing_fcurve = existing_action.fcurves.find(
                    data_path=fcurve.data_path,
                    index=fcurve.array_index
                )
                if existing_fcurve:
                    # Remove the existing fcurve to avoid conflicts
                    existing_action.fcurves.remove(existing_fcurve)
                # Create a new fcurve in the existing action
                new_fcurve = existing_action.fcurves.new(
                    data_path=fcurve.data_path,
                    index=fcurve.array_index,
                    action_group=fcurve.group.name if fcurve.group else None
                )
                # Copy keyframes
                new_fcurve.keyframe_points.add(len(fcurve.keyframe_points))
                for i, kp in enumerate(fcurve.keyframe_points):
                    new_kp = new_fcurve.keyframe_points[i]
                    new_kp.co = kp.co
                    new_kp.handle_left = kp.handle_left
                    new_kp.handle_right = kp.handle_right
                    new_kp.interpolation = kp.interpolation

            # Clean up the temporary action
            if baked_action != temp_action and temp_action:
                bpy.data.actions.remove(temp_action)
            if baked_action:
                bpy.data.actions.remove(baked_action)

            # Ensure the existing action is assigned without triggering read-only error
            if armature.animation_data.action != existing_action:
                try:
                    armature.animation_data.action = existing_action
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to reassign existing action: {str(e)}. Action may need manual reassignment.")

            # Optionally clear the NLA stack and update Animation Layers state
            if self.clear_nla_stack and nla_tracks:
                for track in list(nla_tracks):
                    nla_tracks.remove(track)
                self.report({'INFO'}, "Cleared NLA stack after baking.")
                # Reset Animation Layers' layer_index to prevent out-of-range errors
                if hasattr(armature, 'als') and 'layer_index' in armature.als:
                    armature.als.layer_index = 0
            else:
                self.report({'INFO'}, "Preserved NLA stack after baking.")

        finally:
            # Restore NLA track mute states if not cleared
            if nla_tracks and not self.clear_nla_stack:
                for track, mute_state in track_mute_states.items():
                    track.mute = mute_state

            # Restore the original mode
            bpy.ops.object.mode_set(mode=original_mode)