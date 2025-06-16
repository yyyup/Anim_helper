import bpy

class AH_ConsolidateAudioNLA(bpy.types.Operator):
    """Consolidate NLA strips to single track and align to audio order"""
    bl_idname = "anim.consolidate_audio_nla"
    bl_label = "Consolidate Audio-NLA to Single Track"
    bl_description = "Move all NLA strips to one track and align to audio order with keyword filtering"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Audio filtering
    audio_keyword_filter: bpy.props.StringProperty(
        name="Audio Keyword Filter",
        description="Filter audio by keyword (e.g., 'mark', 'bart'). Only audio containing this will be used for alignment",
        default=""
    )
    
    use_audio_filter: bpy.props.BoolProperty(
        name="Use Audio Keyword Filter",
        description="Only align to audio strips containing the keyword",
        default=False
    )
    
    # Safety options
    target_mode: bpy.props.EnumProperty(
        name="Target Mode",
        items=[
            ('ACTIVE_OBJECT', "Active Object Only", "Only process the active armature and its children"),
            ('CHARACTER_FILTER', "Character Filter", "Process strips matching the character filter"),
            ('SELECTED_OBJECTS', "Selected Objects", "Process selected armatures and meshes")
        ],
        default='ACTIVE_OBJECT'
    )
    
    # Character filter for NLA
    character_filter: bpy.props.StringProperty(
        name="NLA Character Filter",
        description="Filter NLA strips by character (e.g., 'BRI', 'MARK')",
        default=""
    )
    
    # Alignment behavior
    alignment_mode: bpy.props.EnumProperty(
        name="Alignment Mode",
        items=[
            ('MOVE_BOTH', "Move Both Audio & NLA", "Move both audio and NLA to create sequential timeline"),
            ('MOVE_NLA_TO_AUDIO', "Move NLA to Audio", "Keep audio in place, move NLA strips to match audio timing"),
            ('MOVE_AUDIO_TO_NLA', "Move Audio to NLA", "Keep NLA in place, move audio to match NLA timing")
        ],
        default='MOVE_NLA_TO_AUDIO'
    )
    
    # Track naming
    rig_track_name: bpy.props.StringProperty(
        name="Rig Track Name",
        description="Name for the consolidated rig track",
        default="Main_Dialogue_Rig"
    )
    
    shapekey_track_name: bpy.props.StringProperty(
        name="Shape Key Track Name", 
        description="Name for the consolidated shape key track",
        default="Main_Dialogue_Shapes"
    )
    
    # Gap between strips
    strip_gap: bpy.props.FloatProperty(
        name="Gap Between Strips",
        description="Frames between consecutive strips",
        default=10.0,
        min=0.0,
        max=100.0
    )
    
    # Processing options
    process_rig_strips: bpy.props.BoolProperty(
        name="Consolidate Rig Strips",
        description="Move rig/armature NLA strips to single track",
        default=True
    )
    
    process_shapekey_strips: bpy.props.BoolProperty(
        name="Consolidate Shape Key Strips", 
        description="Move shape key NLA strips to single track",
        default=True
    )
    
    # Start time
    start_frame: bpy.props.FloatProperty(
        name="Start Frame",
        description="Frame to start the consolidated sequence",
        default=1.0
    )
    
    # Cleanup options
    remove_original_tracks: bpy.props.BoolProperty(
        name="Delete Original Tracks",
        description="Delete all original tracks after consolidation",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        try:
            # Safety check for character filter mode
            if self.target_mode == 'CHARACTER_FILTER' and not self.character_filter.strip():
                self.report({'ERROR'}, "NLA Character filter is required when using Character Filter mode")
                return {'CANCELLED'}
            
            # Get filtered audio strips
            audio_strips = self.get_filtered_audio_strips(context)
            if not audio_strips and self.use_audio_filter:
                self.report({'ERROR'}, f"No audio strips found matching keyword: '{self.audio_keyword_filter}'")
                return {'CANCELLED'}
            
            # Get all NLA data organized by type
            nla_data = self.get_all_nla_data(context)
            
            if not nla_data['rig_strips'] and not nla_data['shapekey_strips']:
                self.report({'ERROR'}, "No NLA strips found to consolidate")
                return {'CANCELLED'}
            
            # Apply consolidation
            consolidated_count = self.apply_consolidation(context, nla_data, audio_strips)
            
            mode_desc = {
                'MOVE_BOTH': 'sequential timeline',
                'MOVE_NLA_TO_AUDIO': 'NLA aligned to audio positions', 
                'MOVE_AUDIO_TO_NLA': 'audio aligned to NLA positions'
            }
            
            filter_desc = f" (filtered by '{self.audio_keyword_filter}')" if self.use_audio_filter else ""
            self.report({'INFO'}, f"Consolidated {consolidated_count} strips to {mode_desc[self.alignment_mode]} with {len(audio_strips)} audio clips{filter_desc}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error consolidating: {str(e)}")
            return {'CANCELLED'}
    
    def get_filtered_audio_strips(self, context):
        """Get audio strips filtered by keyword and sorted by start frame"""
        if not context.scene.sequence_editor:
            return []
        
        all_audio_strips = [s for s in context.scene.sequence_editor.sequences if s.type == 'SOUND']
        
        # Apply keyword filter if enabled
        if self.use_audio_filter and self.audio_keyword_filter.strip():
            keyword = self.audio_keyword_filter.strip().lower()
            filtered_strips = [s for s in all_audio_strips if keyword in s.name.lower()]
        else:
            filtered_strips = all_audio_strips
        
        # Sort by start frame
        return sorted(filtered_strips, key=lambda s: s.frame_start)
    
    def get_target_objects(self, context):
        """Get target objects based on the selected mode"""
        target_armatures = []
        target_meshes = []
        
        if self.target_mode == 'ACTIVE_OBJECT':
            active = context.active_object
            if not active:
                return [], []
            
            if active.type == 'ARMATURE':
                target_armatures.append(active)
                for child in active.children:
                    if child.type == 'MESH' and child.data.shape_keys:
                        target_meshes.append(child)
            elif active.type == 'MESH' and active.data.shape_keys:
                target_meshes.append(active)
                if active.parent and active.parent.type == 'ARMATURE':
                    target_armatures.append(active.parent)
        
        elif self.target_mode == 'SELECTED_OBJECTS':
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    target_armatures.append(obj)
                elif obj.type == 'MESH' and obj.data.shape_keys:
                    target_meshes.append(obj)
        
        elif self.target_mode == 'CHARACTER_FILTER':
            for obj in context.scene.objects:
                if obj.type == 'ARMATURE':
                    if self.armature_has_character_strips(obj):
                        target_armatures.append(obj)
                elif obj.type == 'MESH' and obj.data.shape_keys:
                    if self.mesh_has_character_strips(obj):
                        target_meshes.append(obj)
        
        return target_armatures, target_meshes
    
    def armature_has_character_strips(self, armature):
        """Check if armature has strips matching character filter"""
        if not armature.animation_data or not armature.animation_data.nla_tracks:
            return False
        
        for track in armature.animation_data.nla_tracks:
            for strip in track.strips:
                if self.character_filter.upper() in strip.name.upper():
                    return True
        return False
    
    def mesh_has_character_strips(self, mesh):
        """Check if mesh has shape key strips matching character filter"""
        if not mesh.data.shape_keys or not mesh.data.shape_keys.animation_data:
            return False
        
        if not mesh.data.shape_keys.animation_data.nla_tracks:
            return False
        
        for track in mesh.data.shape_keys.animation_data.nla_tracks:
            for strip in track.strips:
                if self.character_filter.upper() in strip.name.upper():
                    return True
        return False
    
    def get_all_nla_data(self, context):
        """Get all NLA data organized by type and object"""
        data = {
            'rig_strips': [],
            'rig_objects': [],
            'shapekey_strips': [],
            'shape_objects': []
        }
        
        target_armatures, target_meshes = self.get_target_objects(context)
        
        # Get rig strips from target armatures
        if self.process_rig_strips:
            for obj in target_armatures:
                if obj.animation_data and obj.animation_data.nla_tracks:
                    obj_strips = []
                    for track in obj.animation_data.nla_tracks:
                        for strip in track.strips:
                            # Apply character filter if in character filter mode
                            if (self.target_mode == 'CHARACTER_FILTER' and 
                                self.character_filter.upper() not in strip.name.upper()):
                                continue
                            
                            strip_data = {
                                'strip': strip,
                                'original_track': track,
                                'object': obj,
                                'type': 'rig'
                            }
                            obj_strips.append(strip_data)
                            data['rig_strips'].append(strip_data)
                    
                    if obj_strips:
                        data['rig_objects'].append(obj)
        
        # Get shape key strips from target meshes
        if self.process_shapekey_strips:
            for obj in target_meshes:
                if (obj.data.shape_keys and
                    obj.data.shape_keys.animation_data and
                    obj.data.shape_keys.animation_data.nla_tracks):
                    
                    obj_strips = []
                    for track in obj.data.shape_keys.animation_data.nla_tracks:
                        for strip in track.strips:
                            # Apply character filter if in character filter mode
                            if (self.target_mode == 'CHARACTER_FILTER' and 
                                self.character_filter.upper() not in strip.name.upper()):
                                continue
                            
                            strip_data = {
                                'strip': strip,
                                'original_track': track,
                                'object': obj,
                                'type': 'shapekey'
                            }
                            obj_strips.append(strip_data)
                            data['shapekey_strips'].append(strip_data)
                    
                    if obj_strips:
                        data['shape_objects'].append(obj)
        
        # Sort all strips by current start frame
        data['rig_strips'].sort(key=lambda s: s['strip'].frame_start)
        data['shapekey_strips'].sort(key=lambda s: s['strip'].frame_start)
        
        return data
    
    def apply_consolidation(self, context, nla_data, audio_strips):
        """Apply the consolidation to single tracks"""
        consolidated_count = 0
        
        # Consolidate rig strips
        if nla_data['rig_strips']:
            consolidated_count += self.consolidate_rig_strips(nla_data['rig_strips'], audio_strips)
        
        # Consolidate shape key strips  
        if nla_data['shapekey_strips']:
            consolidated_count += self.consolidate_shapekey_strips(nla_data['shapekey_strips'], audio_strips)
        
        # Clean up original tracks if requested
        if self.remove_original_tracks:
            self.cleanup_original_tracks(nla_data)
        
        return consolidated_count
    
    def consolidate_rig_strips(self, rig_strips, audio_strips):
        """Consolidate all rig strips to one track"""
        if not rig_strips:
            return 0
        
        first_armature = rig_strips[0]['object']
        
        if not first_armature.animation_data:
            first_armature.animation_data_create()
        
        # Create consolidated track
        consolidated_track = first_armature.animation_data.nla_tracks.new()
        consolidated_track.name = self.rig_track_name
        
        strips_moved = 0
        
        for i, strip_data in enumerate(rig_strips):
            strip = strip_data['strip']
            original_track = strip_data['original_track']
            duration = strip.frame_end - strip.frame_start
            
            # Determine frame position based on alignment mode
            if self.alignment_mode == 'MOVE_NLA_TO_AUDIO' and i < len(audio_strips):
                target_frame = audio_strips[i].frame_start
            elif self.alignment_mode == 'MOVE_AUDIO_TO_NLA':
                target_frame = strip.frame_start
            else:  # MOVE_BOTH
                target_frame = self.start_frame + (i * (duration + self.strip_gap))
            
            # Create new strip in consolidated track
            new_strip = consolidated_track.strips.new(
                name=strip.name,
                start=int(target_frame),
                action=strip.action
            )
            
            # Copy strip properties
            new_strip.frame_end = target_frame + duration
            new_strip.blend_in = strip.blend_in
            new_strip.blend_out = strip.blend_out
            new_strip.blend_type = strip.blend_type
            new_strip.extrapolation = strip.extrapolation
            new_strip.influence = strip.influence
            
            # Remove original strip
            original_track.strips.remove(strip)
            
            # Handle audio positioning
            if i < len(audio_strips):
                if self.alignment_mode == 'MOVE_AUDIO_TO_NLA':
                    audio_strips[i].frame_start = target_frame
                elif self.alignment_mode == 'MOVE_BOTH':
                    audio_strips[i].frame_start = target_frame
            
            strips_moved += 1
        
        return strips_moved
    
    def consolidate_shapekey_strips(self, shapekey_strips, audio_strips):
        """Consolidate all shape key strips to one track"""
        if not shapekey_strips:
            return 0
        
        first_mesh = shapekey_strips[0]['object']
        shape_keys = first_mesh.data.shape_keys
        
        if not shape_keys.animation_data:
            shape_keys.animation_data_create()
        
        # Create consolidated track
        consolidated_track = shape_keys.animation_data.nla_tracks.new()
        consolidated_track.name = self.shapekey_track_name
        
        strips_moved = 0
        
        for i, strip_data in enumerate(shapekey_strips):
            strip = strip_data['strip']
            original_track = strip_data['original_track']
            duration = strip.frame_end - strip.frame_start
            
            # Determine frame position based on alignment mode
            if self.alignment_mode == 'MOVE_NLA_TO_AUDIO' and i < len(audio_strips):
                target_frame = audio_strips[i].frame_start
            elif self.alignment_mode == 'MOVE_AUDIO_TO_NLA':
                target_frame = strip.frame_start
            else:  # MOVE_BOTH
                target_frame = self.start_frame + (i * (duration + self.strip_gap))
            
            # Create new strip in consolidated track
            new_strip = consolidated_track.strips.new(
                name=strip.name,
                start=int(target_frame),
                action=strip.action
            )
            
            # Copy strip properties
            new_strip.frame_end = target_frame + duration
            new_strip.blend_in = strip.blend_in
            new_strip.blend_out = strip.blend_out
            new_strip.blend_type = strip.blend_type
            new_strip.extrapolation = strip.extrapolation
            new_strip.influence = strip.influence
            
            # Remove original strip
            original_track.strips.remove(strip)
            strips_moved += 1
        
        return strips_moved
    
    def cleanup_original_tracks(self, nla_data):
        """Remove ALL original tracks after consolidation"""
        # Clean up rig object tracks
        for obj in nla_data['rig_objects']:
            if obj.animation_data and obj.animation_data.nla_tracks:
                tracks_to_remove = []
                for track in obj.animation_data.nla_tracks:
                    if track.name != self.rig_track_name:
                        tracks_to_remove.append(track)
                
                for track in tracks_to_remove:
                    obj.animation_data.nla_tracks.remove(track)
        
        # Clean up shape object tracks
        for obj in nla_data['shape_objects']:
            shape_keys = obj.data.shape_keys
            if shape_keys.animation_data and shape_keys.animation_data.nla_tracks:
                tracks_to_remove = []
                for track in shape_keys.animation_data.nla_tracks:
                    if track.name != self.shapekey_track_name:
                        tracks_to_remove.append(track)
                
                for track in tracks_to_remove:
                    shape_keys.animation_data.nla_tracks.remove(track)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        layout = self.layout
        
        # Audio filtering section
        box = layout.box()
        box.label(text="🎵 Audio Keyword Filtering", icon='SOUND')
        box.prop(self, "use_audio_filter")
        
        if self.use_audio_filter:
            box.prop(self, "audio_keyword_filter")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="Examples: 'mark', 'bart', 'dialogue_01'")
            col.label(text="Only audio containing this keyword will be used")
        
        layout.separator()
        
        # Target mode and safety
        box = layout.box()
        box.label(text="🎯 Target Selection", icon='OUTLINER_OB_ARMATURE')
        box.prop(self, "target_mode")
        
        if self.target_mode == 'CHARACTER_FILTER':
            box.prop(self, "character_filter")
        
        layout.separator()
        
        # Alignment behavior
        box = layout.box()
        box.label(text="🎯 Alignment Behavior", icon='DRIVER')
        box.prop(self, "alignment_mode")
        
        layout.separator()
        
        # Track naming
        box = layout.box()
        box.label(text="Track Names")
        box.prop(self, "rig_track_name")
        box.prop(self, "shapekey_track_name")
        
        layout.separator()
        
        # Processing options
        layout.prop(self, "process_rig_strips")
        layout.prop(self, "process_shapekey_strips")
        layout.separator()
        
        # Timing (only for MOVE_BOTH mode)
        if self.alignment_mode == 'MOVE_BOTH':
            layout.prop(self, "start_frame")
            layout.prop(self, "strip_gap")
            layout.separator()
        
        # Cleanup
        layout.prop(self, "remove_original_tracks")