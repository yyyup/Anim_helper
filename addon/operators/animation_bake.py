import bpy

class AH_AnimationBake(bpy.types.Operator):
    """Bake animations for selected objects and bones with advanced options"""
    bl_idname = "anim_helper.bake_animation"
    bl_label = "Easy Bake Animation"
    bl_description = "Bake animations for selected objects and bones with smart frame detection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type in {'ARMATURE', 'MESH'}
    
    def find_keyframe_range(self, obj):
        """Find the min and max keyframe for an object"""
        min_frame = float('inf')
        max_frame = float('-inf')

        # Check if the object has animation data
        if not obj.animation_data or not obj.animation_data.action:
            return None, None
            
        # Iterate through fcurves to find min/max keyframe
        for fcurve in obj.animation_data.action.fcurves:
            if not fcurve.keyframe_points:
                continue
                
            keyframes = [keyframe.co[0] for keyframe in fcurve.keyframe_points]
            if keyframes:
                min_frame = min(min(keyframes), min_frame)
                max_frame = max(max(keyframes), max_frame)

        if min_frame == float('inf'):
            return None, None
        return min_frame, max_frame
    
    def execute(self, context):
        bprops = context.scene.bprops
        
        # Keep track of successfully baked objects
        baked_objects = 0
        
        # Process each selected object
        for obj in context.selected_objects:
            # Skip objects that aren't armatures or meshes
            if obj.type not in {'ARMATURE', 'MESH'}:
                continue
                
            context.view_layer.objects.active = obj
            
            # Get frame range
            if bprops.smart_bake:
                min_frame, max_frame = self.find_keyframe_range(obj)
                if min_frame is None:
                    self.report({'WARNING'}, f"No keyframes found for {obj.name}, skipping.")
                    continue
            else:
                min_frame, max_frame = bprops.custom_frame_start, bprops.custom_frame_end

            # Process armature objects
            if obj.type == 'ARMATURE':
                bpy.ops.object.mode_set(mode='POSE')
                
                # Get all selected bones
                bones = [bone for bone in obj.pose.bones if bone.bone.select]
                
                if not bones and bprops.only_selected_bones:
                    self.report({'WARNING'}, f"No bones selected in {obj.name}, skipping.")
                    bpy.ops.object.mode_set(mode='OBJECT')
                    continue
                
                try:
                    bpy.ops.nla.bake(
                        frame_start=int(min_frame), 
                        frame_end=int(max_frame), 
                        only_selected=bprops.only_selected_bones,
                        visual_keying=bprops.visual_keying, 
                        clear_constraints=bprops.clear_constraints, 
                        use_current_action=bprops.overwrite_current_action, 
                        clear_parents=bprops.clear_parents,
                        bake_types={'POSE'}
                    )
                    baked_objects += 1
                except Exception as e:
                    self.report({'ERROR'}, f"Error baking {obj.name}: {str(e)}")
                
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Process mesh objects
            elif obj.type == 'MESH':
                try:
                    bpy.ops.nla.bake(
                        frame_start=int(min_frame),
                        frame_end=int(max_frame),
                        visual_keying=bprops.visual_keying,
                        clear_constraints=bprops.clear_constraints,
                        use_current_action=bprops.overwrite_current_action,
                        clear_parents=bprops.clear_parents,
                        bake_types={'OBJECT'}
                    )
                    baked_objects += 1
                except Exception as e:
                    self.report({'ERROR'}, f"Error baking {obj.name}: {str(e)}")

        if baked_objects > 0:
            self.report({'INFO'}, f"Baking complete! Successfully baked {baked_objects} objects.")
        else:
            self.report({'WARNING'}, "No objects were baked. Check selection and animation data.")
            
        return {'FINISHED'}