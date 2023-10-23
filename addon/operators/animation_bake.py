import bpy
import bpy.props


class bakeprops(bpy.types.PropertyGroup):
    smart_bake : bpy.props.BoolProperty(name="Smart Bake", default=True, description="Automatically detect keyframes for baking")
    custom_frame_start : bpy.props.IntProperty(name="Custom Start Frame", default=1, description="Specify start frame for baking")
    custom_frame_end : bpy.props.IntProperty(name="Custom End Frame", default=250, description="Specify end frame for baking")
    only_selected_bones: bpy.props.BoolProperty(name="Only Selected Bones", default=True)
    visual_keying: bpy.props.BoolProperty(name="Visual Keying", default=True)
    clear_constraints: bpy.props.BoolProperty(name="Clear Constraints", default=True)
    clear_parents: bpy.props.BoolProperty(name="Clear Parents", default=True)
    overwrite_current_action: bpy.props.BoolProperty(name="Overwrite Current Action", default=True)
        



class AH_Animation_bake(bpy.types.Operator):
    """Bake animations for selected objects and bones"""
    
    
    
    bl_idname = "anim_helper.bake_animation"
    bl_label = "ezbake"
    bl_description = "Bake animations for selected objects and bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type in {'ARMATURE', 'MESH'}
    
    def find_keyframe_range(self, obj):
        min_frame = float('inf')
        max_frame = float('-inf')

        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                keyframes = [keyframe.co[0] for keyframe in fcurve.keyframe_points]
                min_frame = min(min(keyframes), min_frame)
                max_frame = max(max(keyframes), max_frame)

        if min_frame == float('inf'):
            return None, None
        return min_frame, max_frame
    
    def execute(self, context):
        
        bprops = context.scene.bprops
        
        
        
        
        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = obj
            
            if bprops.smart_bake:
                min_frame, max_frame = self.find_keyframe_range(obj)
            else:
                min_frame, max_frame = bprops.custom_frame_start, bprops.custom_frame_end

            if obj.type == 'ARMATURE':
                bpy.ops.object.mode_set(mode='POSE')
                
                bones = [bone for bone in obj.pose.bones if bone.bone.select]
                    
                for bone in bones:
                    bone.bone.select = True
                    
                    if min_frame is not None:
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
                        
                bpy.ops.object.mode_set(mode='OBJECT')

            elif obj.type == 'MESH':
                if min_frame is not None:
                    bpy.ops.nla.bake(
                        frame_start=int(min_frame),
                        frame_end=int(max_frame),
                        visual_keying=bprops.visual_keying,
                        clear_constraints=bprops.clear_constraints,
                        use_current_action=bprops.overwrite_current_action,
                        clear_parents=bprops.clear_parents,
                        bake_types={'OBJECT'}
                    )

        self.report({'INFO'}, "Baking Complete!")
        return {'FINISHED'}
    
    
    

 
