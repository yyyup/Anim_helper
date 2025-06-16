import bpy

class AH_CopyTransforms(bpy.types.Operator):
    """Create empty objects that copy and can reverse the transforms of selected bones or mesh objects"""
    bl_idname = "anim_h.copy_t"
    bl_label = "Copy Transforms with Reverse"
    bl_description = "Space switch: Create empties that copy transforms for advanced animation control"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Check what's selected and active
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'WARNING'}, "No active object selected.")
            return {'CANCELLED'}
            
        # Handle armatures with pose bones
        if active_obj.type == 'ARMATURE' and context.mode == 'POSE':
            return self.process_bones(context)
        # Handle mesh objects
        elif context.selected_objects:
            return self.process_mesh_objects(context)
        else:
            self.report({'WARNING'}, "Please select an armature in pose mode or mesh objects.")
            return {'CANCELLED'}

    def exit_nla_tweak_mode(self, context, obj):
        """Safely exit NLA tweak mode if active, compatible across Blender versions."""
        if not obj.animation_data or not obj.animation_data.nla_tracks:
            return

        # Check for tweak mode using a more compatible approach
        try:
            # In Blender 3.2+, use is_tweakmode
            if hasattr(obj.animation_data, 'is_tweakmode') and obj.animation_data.is_tweakmode:
                bpy.ops.nla.tweakmode_exit()
        except AttributeError:
            # For older Blender versions, check if any strip is being edited
            for track in obj.animation_data.nla_tracks:
                if track.is_solo or track.mute:
                    continue
                for strip in track.strips:
                    if strip.active:
                        # Attempt to exit tweak mode by toggling
                        bpy.ops.nla.tweakmode_enter()
                        bpy.ops.nla.tweakmode_exit()
                        break
                break

    def bake_full_stack(self, context, obj, frame_start, frame_end, bake_types='OBJECT'):
        """Bake the full NLA stack into a new action for the given object."""
        if not obj.animation_data:
            return None

        # Check if there are NLA tracks to bake
        nla_tracks = obj.animation_data.nla_tracks
        original_action = obj.animation_data.action if obj.animation_data else None
        baked_action = None

        try:
            # Exit tweak mode if active
            self.exit_nla_tweak_mode(context, obj)

            # Mute all NLA tracks to isolate the baking (without modifying action)
            track_mute_states = {}
            if nla_tracks:
                for track in nla_tracks:
                    track_mute_states[track] = track.mute
                    track.mute = True

            # Create a temporary empty to bake the full stack
            temp_empty = bpy.data.objects.new(f"TEMP_Bake_{obj.name}", None)
            context.collection.objects.link(temp_empty)

            # Ensure the temporary empty has animation data
            if not temp_empty.animation_data:
                temp_empty.animation_data_create()

            # Add a Copy Transforms constraint to capture the object's animation
            constraint = temp_empty.constraints.new(type='COPY_TRANSFORMS')
            if bake_types == 'POSE' and obj.type == 'ARMATURE':
                # For pose baking, we'll bake directly on the armature
                temp_empty.constraints.remove(constraint)
            else:
                constraint.target = obj

            # Unmute NLA tracks to evaluate the full stack during baking
            if nla_tracks:
                for track in nla_tracks:
                    track.mute = track_mute_states[track]

            # Bake the full stack
            bpy.ops.object.select_all(action='DESELECT')
            if bake_types == 'POSE':
                obj.select_set(True)
                context.view_layer.objects.active = obj
            else:
                temp_empty.select_set(True)
                context.view_layer.objects.active = temp_empty

            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=False,
                bake_types={bake_types}
            )

            # Retrieve the baked action
            if bake_types == 'POSE':
                baked_action = obj.animation_data.action
            else:
                baked_action = temp_empty.animation_data.action

            # Clean up
            if temp_empty.constraints:
                temp_empty.constraints.remove(constraint)
            bpy.data.objects.remove(temp_empty, do_unlink=True)

        except Exception as e:
            self.report({'ERROR'}, f"Failed to bake full NLA stack: {str(e)}")
            return None
        finally:
            # Restore NLA track mute states
            if nla_tracks:
                for track, mute_state in track_mute_states.items():
                    track.mute = mute_state

        return baked_action

    def find_armature_frame_range(self, armature, bones):
        """Find the animation frame range for bones in an armature, considering the full NLA stack."""
        min_frame = float('inf')
        max_frame = float('-inf')
        has_animation = False
        
        # Check for direct action keyframes on the specific bones
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            for bone in bones:
                bone_path = f'pose.bones["{bone.name}"]'
                for fcurve in action.fcurves:
                    if bone_path in fcurve.data_path and fcurve.keyframe_points:
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
                    
        # Check for object animation on the armature itself
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
        else:
            return 0, 0, False
            
    def find_object_frame_range(self, obj):
        """Recursively find the animation frame range from an object and its parents, considering the full NLA stack."""
        min_frame = float('inf')
        max_frame = float('-inf')
        has_animation = False
        
        # Check the object's own action
        if obj.animation_data and obj.animation_data.action:
            has_animation = True
            action = obj.animation_data.action
            for fcurve in action.fcurves:
                if fcurve.keyframe_points:
                    for keyframe in fcurve.keyframe_points:
                        min_frame = min(min_frame, keyframe.co.x)
                        max_frame = max(max_frame, keyframe.co.x)
        
        # Check NLA strips
        if obj.animation_data and obj.animation_data.nla_tracks:
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    has_animation = True
                    min_frame = min(min_frame, strip.frame_start)
                    max_frame = max(max_frame, strip.frame_end)
                        
        # Check the parent recursively
        if obj.parent:
            parent_min, parent_max, parent_has_anim = self.find_object_frame_range(obj.parent)
            if parent_has_anim:
                min_frame = min(min_frame, parent_min)
                max_frame = max(max_frame, parent_max)
                has_animation = True
                
        # Check constraints
        for constraint in obj.constraints:
            if constraint.type in {'FOLLOW_PATH', 'TRACK_TO'} and constraint.target:
                target_min, target_max, target_has_anim = self.find_object_frame_range(constraint.target)
                if target_has_anim:
                    min_frame = min(min_frame, target_min)
                    max_frame = max(max_frame, target_max)
                    has_animation = True
                    break
        
        if has_animation:
            return int(min_frame), int(max_frame), True
        else:
            return 0, 0, False
            
    def process_bones(self, context):
        """Handle selected pose bones"""
        selected_bones = context.selected_pose_bones
        
        if not selected_bones or len(selected_bones) == 0:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}
        
        # Detect frame range from animation
        armature = selected_bones[0].id_data
        min_frame, max_frame, has_animation = self.find_armature_frame_range(armature, selected_bones)
        
        if not has_animation:
            min_frame = context.scene.frame_start
            max_frame = context.scene.frame_end
            self.report({'INFO'}, f"No direct animation found. Using scene frame range: {min_frame} to {max_frame}")
        else:
            self.report({'INFO'}, f"Found animation frame range: {min_frame} to {max_frame}")
        
        # Create empties for the selected bones
        created_empties = []
        try:
            # Bake the full stack for the armature to ensure all layers are captured
            baked_action = self.bake_full_stack(context, armature, min_frame, max_frame, bake_types='POSE')

            # Create an empty for each selected bone
            for bone in selected_bones:
                empty = bpy.data.objects.new(f"CopyT_{bone.name}", None)
                bone_matrix_world = armature.matrix_world @ bone.matrix
                empty.matrix_world = bone_matrix_world
                empty.rotation_mode = bone.rotation_mode
                
                context.collection.objects.link(empty)

                # Assign the baked action to the empty if available, or use a constraint
                if baked_action:
                    if not empty.animation_data:
                        empty.animation_data_create()
                    empty.animation_data.action = baked_action.copy()  # Use a copy to avoid sharing
                else:
                    constraint = empty.constraints.new(type="COPY_TRANSFORMS")
                    constraint.target = armature
                    constraint.subtarget = bone.name

                created_empties.append(empty)

            # Bake the empties' animation
            original_active_object = context.active_object
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            for empty in created_empties:
                empty.select_set(True)
            context.view_layer.objects.active = created_empties[0]

            bpy.ops.nla.bake(
                frame_start=min_frame,
                frame_end=max_frame,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                use_current_action=True,
                bake_types={"OBJECT"}
            )

            # Switch back to pose mode
            context.view_layer.objects.active = original_active_object
            bpy.ops.object.mode_set(mode='POSE')

            # Add Copy Transforms constraints to the bones
            for i, bone in enumerate(selected_bones):
                if i < len(created_empties):
                    constraint = bone.constraints.new(type="COPY_TRANSFORMS")
                    constraint.target = created_empties[i]
            
            self.report({'INFO'}, f"Created and baked {len(created_empties)} empties for bone transform control.")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating transform controls for bones: {str(e)}")
            return {'CANCELLED'}
            
    def process_mesh_objects(self, context):
        """Handle selected mesh objects"""
        selected_objects = [obj for obj in context.selected_objects if obj.type in {'MESH', 'EMPTY', 'CURVE', 'ARMATURE'}]
        
        if not selected_objects:
            self.report({'WARNING'}, "No suitable objects selected.")
            return {'CANCELLED'}
            
        # Find frame range from all selected objects and their parents
        min_frame = float('inf')
        max_frame = float('-inf')
        has_animation = False
        
        for obj in selected_objects:
            obj_min, obj_max, obj_has_anim = self.find_object_frame_range(obj)
            if obj_has_anim:
                has_animation = True
                min_frame = min(min_frame, obj_min)
                max_frame = max(max_frame, obj_max)
        
        if not has_animation:
            min_frame = context.scene.frame_start
            max_frame = context.scene.frame_end
            self.report({'INFO'}, f"No direct animation found. Using scene frame range: {min_frame} to {max_frame}")
        else:
            self.report({'INFO'}, f"Found animation frame range: {min_frame} to {max_frame}")
            
        # Create empties for the selected objects
        created_empties = []
        try:
            # Bake the full stack for each selected object
            for obj in selected_objects:
                baked_action = self.bake_full_stack(context, obj, min_frame, max_frame)

                empty = bpy.data.objects.new(f"CopyT_{obj.name}", None)
                empty.matrix_world = obj.matrix_world.copy()
                empty.rotation_mode = obj.rotation_mode
                context.collection.objects.link(empty)

                # Assign the baked action to the empty if available, or use a constraint
                if baked_action:
                    if not empty.animation_data:
                        empty.animation_data_create()
                    empty.animation_data.action = baked_action.copy()  # Use a copy to avoid sharing
                else:
                    constraint = empty.constraints.new(type="COPY_TRANSFORMS")
                    constraint.target = obj

                created_empties.append({
                    "empty": empty,
                    "original": obj
                })

            # Bake the empties' animation
            original_active_object = context.active_object
            bpy.ops.object.select_all(action='DESELECT')

            for item in created_empties:
                item["empty"].select_set(True)
            context.view_layer.objects.active = created_empties[0]["empty"]

            bpy.ops.nla.bake(
                frame_start=min_frame,
                frame_end=max_frame,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                use_current_action=True,
                bake_types={"OBJECT"}
            )

            # Restore original selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            context.view_layer.objects.active = original_active_object

            # Add Copy Transforms constraints to the original objects
            for item in created_empties:
                constraint = item["original"].constraints.new(type="COPY_TRANSFORMS")
                constraint.target = item["empty"]
            
            self.report({'INFO'}, f"Created and baked {len(created_empties)} empties for object transform control.")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating transform controls for objects: {str(e)}")
            return {'CANCELLED'}