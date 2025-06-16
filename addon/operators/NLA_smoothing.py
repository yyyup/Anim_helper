import bpy

class AH_NLASmoothTransitions(bpy.types.Operator):
    """Smooth facial animation transitions in NLA strips to reduce head popping"""
    bl_idname = "anim.nla_smooth_transitions"
    bl_label = "Smooth NLA Transitions"
    bl_description = "Add blending to NLA strips to smooth facial animation transitions (SELECTED OBJECTS ONLY)"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Properties
    blend_frames: bpy.props.IntProperty(
        name="Blend Frames",
        description="Number of frames to blend at strip transitions",
        default=5,
        min=1,
        max=20
    )
    
    process_armature: bpy.props.BoolProperty(
        name="Process Armature",
        description="Fix armature/bone transitions",
        default=True
    )
    
    process_shapekeys: bpy.props.BoolProperty(
        name="Process Shape Keys", 
        description="Fix shape key transitions",
        default=True
    )
    
    selected_tracks_only: bpy.props.BoolProperty(
        name="Selected Tracks Only",
        description="Only process tracks with selected strips (within selected objects)",
        default=False
    )
    
    @classmethod
    def poll(cls, context):
        # Require at least one selected object
        return len(context.selected_objects) > 0
    
    def execute(self, context):
        # Get only selected objects
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected. Please select armatures or meshes to process.")
            return {'CANCELLED'}
        
        try:
            armature_strips = 0
            shapekey_strips = 0
            
            if self.process_armature:
                armature_strips = self.process_selected_armature_transitions(selected_objects)
            
            if self.process_shapekeys:
                shapekey_strips = self.process_selected_shapekey_transitions(selected_objects)
            
            total_strips = armature_strips + shapekey_strips
            
            if total_strips > 0:
                object_names = [obj.name for obj in selected_objects]
                message = f"Applied blending to {armature_strips} armature strips, {shapekey_strips} shape key strips on selected objects: {', '.join(object_names[:3])}"
                if len(object_names) > 3:
                    message += f" and {len(object_names) - 3} more"
                self.report({'INFO'}, message)
            else:
                self.report({'WARNING'}, "No strips processed. Check selected objects and settings.")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error smoothing transitions: {str(e)}")
            return {'CANCELLED'}
    
    def process_selected_armature_transitions(self, selected_objects):
        """Process armature NLA transitions for selected objects only"""
        strips_processed = 0
        
        # Only process selected armatures
        selected_armatures = [obj for obj in selected_objects if obj.type == 'ARMATURE']
        
        for armature in selected_armatures:
            if not armature.animation_data or not armature.animation_data.nla_tracks:
                continue
            
            print(f"Processing selected armature: {armature.name}")
            
            for track in armature.animation_data.nla_tracks:
                # Skip if only processing selected tracks and none are selected
                if self.selected_tracks_only:
                    has_selected = any(strip.select for strip in track.strips)
                    if not has_selected:
                        continue
                
                strips = sorted(track.strips, key=lambda s: s.frame_start)
                
                if len(strips) < 2:
                    continue
                
                strips_processed += self.apply_strip_blending(strips, armature.name, track.name)
        
        return strips_processed
    
    def process_selected_shapekey_transitions(self, selected_objects):
        """Process shape key NLA transitions for selected objects only"""
        strips_processed = 0
        
        # Only process selected meshes with shape keys
        selected_meshes = [obj for obj in selected_objects 
                          if obj.type == 'MESH' and obj.data.shape_keys]
        
        for mesh in selected_meshes:
            shape_keys = mesh.data.shape_keys
            if not shape_keys.animation_data or not shape_keys.animation_data.nla_tracks:
                continue
            
            print(f"Processing selected mesh shape keys: {mesh.name}")
            
            for track in shape_keys.animation_data.nla_tracks:
                # Skip if only processing selected tracks and none are selected
                if self.selected_tracks_only:
                    has_selected = any(strip.select for strip in track.strips)
                    if not has_selected:
                        continue
                
                strips = sorted(track.strips, key=lambda s: s.frame_start)
                
                if len(strips) < 2:
                    continue
                
                strips_processed += self.apply_strip_blending(strips, mesh.name, track.name)
        
        return strips_processed
    
    def apply_strip_blending(self, strips, object_name, track_name):
        """Apply blending to a list of strips"""
        strips_processed = 0
        
        for i, strip in enumerate(strips):
            # Skip if only processing selected and this isn't selected
            if self.selected_tracks_only and not strip.select:
                continue
            
            strip_length = strip.frame_end - strip.frame_start
            max_blend = max(1, int(strip_length * 0.2))  # Max 20% of strip length
            blend_amount = min(self.blend_frames, max_blend)
            
            # Apply blend-in (except first strip)
            if i > 0:
                strip.blend_in = blend_amount
                print(f"  Applied blend_in={blend_amount} to '{strip.name}' in {object_name}/{track_name}")
            
            # Apply blend-out (except last strip)
            if i < len(strips) - 1:
                strip.blend_out = blend_amount
                print(f"  Applied blend_out={blend_amount} to '{strip.name}' in {object_name}/{track_name}")
            
            # Use REPLACE mode - facial actions should override base animation
            strip.blend_type = 'REPLACE'
            strips_processed += 1
        
        return strips_processed
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        
        # Show selected objects info
        selected_objects = context.selected_objects
        armatures = [obj for obj in selected_objects if obj.type == 'ARMATURE']
        meshes = [obj for obj in selected_objects if obj.type == 'MESH' and obj.data.shape_keys]
        
        box = layout.box()
        box.label(text="Selected Objects:", icon='RESTRICT_SELECT_OFF')
        col = box.column(align=True)
        col.scale_y = 0.8
        
        if armatures:
            col.label(text=f"Armatures: {len(armatures)}")
            for arm in armatures[:3]:
                col.label(text=f"  • {arm.name}")
            if len(armatures) > 3:
                col.label(text=f"  ... and {len(armatures) - 3} more")
        
        if meshes:
            col.label(text=f"Meshes with shape keys: {len(meshes)}")
            for mesh in meshes[:3]:
                col.label(text=f"  • {mesh.name}")
            if len(meshes) > 3:
                col.label(text=f"  ... and {len(meshes) - 3} more")
        
        if not armatures and not meshes:
            col.alert = True
            col.label(text="No armatures or shape key meshes selected!")
        
        layout.separator()
        
        layout.prop(self, "blend_frames")
        layout.separator()
        
        layout.prop(self, "process_armature")
        layout.prop(self, "process_shapekeys")
        layout.separator()
        
        layout.prop(self, "selected_tracks_only")


class AH_NLACleanTransitions(bpy.types.Operator):
    """Remove all blending from NLA strips on selected objects"""
    bl_idname = "anim.nla_clean_transitions"
    bl_label = "Clean NLA Transitions"
    bl_description = "Remove all blending from NLA strips and reset to default state (SELECTED OBJECTS ONLY)"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}
        
        strips_cleaned = 0
        
        # Clean armature strips on selected objects only
        selected_armatures = [obj for obj in selected_objects if obj.type == 'ARMATURE']
        for armature in selected_armatures:
            if armature.animation_data and armature.animation_data.nla_tracks:
                for track in armature.animation_data.nla_tracks:
                    for strip in track.strips:
                        strip.blend_in = 0
                        strip.blend_out = 0
                        strip.blend_type = 'REPLACE'
                        strips_cleaned += 1
        
        # Clean shape key strips on selected objects only
        selected_meshes = [obj for obj in selected_objects 
                          if obj.type == 'MESH' and obj.data.shape_keys]
        for mesh in selected_meshes:
            shape_keys = mesh.data.shape_keys
            if shape_keys.animation_data and shape_keys.animation_data.nla_tracks:
                for track in shape_keys.animation_data.nla_tracks:
                    for strip in track.strips:
                        strip.blend_in = 0
                        strip.blend_out = 0
                        strip.blend_type = 'REPLACE'
                        strips_cleaned += 1
        
        object_names = [obj.name for obj in selected_objects]
        message = f"Cleaned {strips_cleaned} strips on selected objects: {', '.join(object_names[:3])}"
        if len(object_names) > 3:
            message += f" and {len(object_names) - 3} more"
        
        self.report({'INFO'}, message)
        return {'FINISHED'}