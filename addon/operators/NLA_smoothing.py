import bpy

class AH_NLASmoothTransitions(bpy.types.Operator):
    """Smooth facial animation transitions in NLA strips to reduce head popping"""
    bl_idname = "anim.nla_smooth_transitions"
    bl_label = "Smooth NLA Transitions"
    bl_description = "Add blending to NLA strips to smooth facial animation transitions"
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
    
    process_all_tracks: bpy.props.BoolProperty(
        name="Process ALL Tracks",
        description="Process all NLA tracks regardless of name",
        default=True
    )
    
    selected_tracks_only: bpy.props.BoolProperty(
        name="Selected Tracks Only",
        description="Only process tracks with selected strips",
        default=False
    )
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        try:
            armature_strips = 0
            shapekey_strips = 0
            
            if self.process_armature:
                armature_strips = self.process_armature_transitions(context)
            
            if self.process_shapekeys:
                shapekey_strips = self.process_shapekey_transitions(context)
            
            total_strips = armature_strips + shapekey_strips
            
            if total_strips > 0:
                message = f"Applied blending to {armature_strips} armature strips, {shapekey_strips} shape key strips"
                self.report({'INFO'}, message)
            else:
                self.report({'WARNING'}, "No strips processed. Check your NLA setup and settings.")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error smoothing transitions: {str(e)}")
            return {'CANCELLED'}
    
    def should_process_track(self, track):
        """Determine if we should process this track"""
        # If only processing selected tracks, check for selected strips
        if self.selected_tracks_only:
            return any(strip.select for strip in track.strips)
        
        # If processing all tracks, return True
        if self.process_all_tracks:
            return True
        
        # Otherwise, use keyword detection
        keywords = [
            'facial', 'speech', 'head', 'rig', 'shape', 'key',
            'cc_', 'bri', 'ra_', 'sa_',  # Common naming patterns
            'action', 'track', 'test'
        ]
        
        track_lower = track.name.lower()
        return any(keyword in track_lower for keyword in keywords)
    
    def process_armature_transitions(self, context):
        """Process armature NLA transitions"""
        strips_processed = 0
        
        for obj in context.scene.objects:
            if obj.type != 'ARMATURE':
                continue
                
            if not obj.animation_data or not obj.animation_data.nla_tracks:
                continue
            
            for track in obj.animation_data.nla_tracks:
                if not self.should_process_track(track):
                    continue
                
                strips = sorted(track.strips, key=lambda s: s.frame_start)
                
                if len(strips) < 2:
                    continue
                
                strips_processed += self.apply_strip_blending(strips)
        
        return strips_processed
    
    def process_shapekey_transitions(self, context):
        """Process shape key NLA transitions"""
        strips_processed = 0
        
        for obj in context.scene.objects:
            if obj.type != 'MESH' or not obj.data.shape_keys:
                continue
            
            shape_keys = obj.data.shape_keys
            if not shape_keys.animation_data or not shape_keys.animation_data.nla_tracks:
                continue
            
            for track in shape_keys.animation_data.nla_tracks:
                if not self.should_process_track(track):
                    continue
                
                strips = sorted(track.strips, key=lambda s: s.frame_start)
                
                if len(strips) < 2:
                    continue
                
                strips_processed += self.apply_strip_blending(strips)
        
        return strips_processed
    
    def apply_strip_blending(self, strips):
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
            
            # Apply blend-out (except last strip)
            if i < len(strips) - 1:
                strip.blend_out = blend_amount
            
            # Use REPLACE mode - facial actions should override base animation
            strip.blend_type = 'REPLACE'
            strips_processed += 1
        
        return strips_processed
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        
        layout.prop(self, "blend_frames")
        layout.separator()
        
        layout.prop(self, "process_armature")
        layout.prop(self, "process_shapekeys")
        layout.separator()
        
        layout.prop(self, "process_all_tracks")
        layout.prop(self, "selected_tracks_only")


class AH_NLACleanTransitions(bpy.types.Operator):
    """Remove all blending from NLA strips"""
    bl_idname = "anim.nla_clean_transitions"
    bl_label = "Clean NLA Transitions"
    bl_description = "Remove all blending from NLA strips and reset to default state"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        strips_cleaned = 0
        
        # Clean armature strips
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE' and obj.animation_data and obj.animation_data.nla_tracks:
                for track in obj.animation_data.nla_tracks:
                    for strip in track.strips:
                        strip.blend_in = 0
                        strip.blend_out = 0
                        strip.blend_type = 'REPLACE'
                        strips_cleaned += 1
        
        # Clean shape key strips
        for obj in context.scene.objects:
            if (obj.type == 'MESH' and 
                obj.data.shape_keys and 
                obj.data.shape_keys.animation_data and
                obj.data.shape_keys.animation_data.nla_tracks):
                for track in obj.data.shape_keys.animation_data.nla_tracks:
                    for strip in track.strips:
                        strip.blend_in = 0
                        strip.blend_out = 0
                        strip.blend_type = 'REPLACE'
                        strips_cleaned += 1
        
        self.report({'INFO'}, f"Cleaned {strips_cleaned} strips")
        return {'FINISHED'}