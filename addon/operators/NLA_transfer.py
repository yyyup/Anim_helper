import bpy

class AH_TransferNLAStrips(bpy.types.Operator):
    """Transfer NLA strips from source object to target object with safe positioning"""
    bl_idname = "anim.transfer_nla_strips_fixed"
    bl_label = "Transfer NLA Strips (Safe)"
    bl_description = "Copy NLA strips from active object to selected objects without affecting existing strips"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Properties for different transfer modes
    transfer_mode: bpy.props.EnumProperty(
        name="Transfer Mode",
        items=[
            ('NEW_TRACKS', "New Tracks Only", "Always create new tracks, never modify existing ones"),
            ('APPEND', "Append to Existing", "Add to existing tracks if they exist"),
            ('REPLACE', "Replace Tracks", "Replace tracks with same name"),
        ],
        default='NEW_TRACKS'
    )
    
    preserve_timing: bpy.props.BoolProperty(
        name="Preserve Source Timing",
        description="Keep original strip timing from source object",
        default=True
    )
    
    mute_new_tracks: bpy.props.BoolProperty(
        name="Mute New Tracks",
        description="Automatically mute the transferred tracks",
        default=True
    )
    
    track_prefix: bpy.props.StringProperty(
        name="Track Prefix",
        description="Prefix for new track names to avoid conflicts",
        default="Transferred_"
    )
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.animation_data is not None and
                len(context.selected_objects) >= 2)
    
    def execute(self, context):
        source_obj = context.active_object
        target_objects = [obj for obj in context.selected_objects 
                         if obj != source_obj and obj.type == 'ARMATURE']
        
        if not target_objects:
            self.report({'ERROR'}, "Select source (active) and target armature(s)")
            return {'CANCELLED'}
        
        if not source_obj.animation_data or not source_obj.animation_data.nla_tracks:
            self.report({'ERROR'}, "Source object has no NLA tracks")
            return {'CANCELLED'}
        
        strips_copied = 0
        tracks_created = 0
        
        for target_obj in target_objects:
            # Ensure target has animation data
            if not target_obj.animation_data:
                target_obj.animation_data_create()
            
            # Store existing tracks to avoid modifying them
            existing_tracks = list(target_obj.animation_data.nla_tracks)
            existing_track_names = {track.name for track in existing_tracks}
            
            # Copy each NLA track from source to target
            for source_track in source_obj.animation_data.nla_tracks:
                target_track = None
                
                if self.transfer_mode == 'NEW_TRACKS':
                    # Always create new track with unique name
                    track_name = self.get_unique_track_name(target_obj, source_track.name)
                    target_track = target_obj.animation_data.nla_tracks.new()
                    target_track.name = track_name
                    tracks_created += 1
                    
                elif self.transfer_mode == 'APPEND':
                    # Look for existing track with same name
                    for existing_track in target_obj.animation_data.nla_tracks:
                        if existing_track.name == source_track.name:
                            target_track = existing_track
                            break
                    
                    # Create new track if not found
                    if target_track is None:
                        target_track = target_obj.animation_data.nla_tracks.new()
                        target_track.name = source_track.name
                        tracks_created += 1
                        
                elif self.transfer_mode == 'REPLACE':
                    # Remove existing track with same name
                    for existing_track in list(target_obj.animation_data.nla_tracks):
                        if existing_track.name == source_track.name:
                            target_obj.animation_data.nla_tracks.remove(existing_track)
                            break
                    
                    # Create new track
                    target_track = target_obj.animation_data.nla_tracks.new()
                    target_track.name = source_track.name
                    tracks_created += 1
                
                # Copy track properties (only for new tracks)
                if target_track and target_track not in existing_tracks:
                    target_track.mute = self.mute_new_tracks
                    target_track.lock = source_track.lock
                    if hasattr(source_track, 'solo'):
                        target_track.solo = source_track.solo
                
                # Copy each strip in the track
                for source_strip in source_track.strips:
                    # Create action copy to avoid sharing references
                    if source_strip.action:
                        action_copy = source_strip.action.copy()
                        action_copy.name = f"{source_strip.action.name}_Copy"
                    else:
                        action_copy = None
                    
                    # Determine strip timing
                    if self.preserve_timing:
                        start_frame = source_strip.frame_start
                    else:
                        # Place after existing strips in target track
                        start_frame = self.get_next_available_frame(target_track)
                    
                    # Create new strip
                    target_strip = target_track.strips.new(
                        name=source_strip.name,
                        start=int(start_frame),
                        action=action_copy
                    )
                    
                    # Copy strip properties
                    target_strip.frame_end = source_strip.frame_end
                    target_strip.extrapolation = source_strip.extrapolation
                    target_strip.blend_type = source_strip.blend_type
                    target_strip.influence = source_strip.influence
                    target_strip.mute = source_strip.mute
                    target_strip.use_reverse = source_strip.use_reverse
                    
                    # Copy blend settings
                    target_strip.blend_in = source_strip.blend_in
                    target_strip.blend_out = source_strip.blend_out
                    
                    strips_copied += 1
        
        self.report({'INFO'}, f"Created {tracks_created} tracks, copied {strips_copied} strips to {len(target_objects)} objects")
        return {'FINISHED'}
    
    def get_unique_track_name(self, target_obj, base_name):
        """Generate unique track name to avoid conflicts"""
        existing_names = {track.name for track in target_obj.animation_data.nla_tracks}
        
        # Try with prefix first
        prefixed_name = f"{self.track_prefix}{base_name}"
        if prefixed_name not in existing_names:
            return prefixed_name
        
        # Add number suffix if needed
        counter = 1
        while f"{prefixed_name}_{counter:03d}" in existing_names:
            counter += 1
        
        return f"{prefixed_name}_{counter:03d}"
    
    def get_next_available_frame(self, track):
        """Find the next available frame after existing strips"""
        if not track.strips:
            return 1
        
        latest_end = max(strip.frame_end for strip in track.strips)
        return int(latest_end) + 10  # 10 frame gap
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def draw(self, context):
        layout = self.layout
        
        # Show selected objects
        source = context.active_object
        targets = [obj for obj in context.selected_objects 
                  if obj != source and obj.type == 'ARMATURE']
        
        box = layout.box()
        box.label(text="Transfer Setup:", icon='NLA')
        col = box.column(align=True)
        col.scale_y = 0.8
        
        if source:
            col.label(text=f"Source: {source.name}")
            if source.animation_data and source.animation_data.nla_tracks:
                col.label(text=f"  • {len(source.animation_data.nla_tracks)} NLA tracks")
        
        if targets:
            col.label(text=f"Targets: {', '.join([obj.name for obj in targets])}")
        else:
            col.alert = True
            col.label(text="No target armatures selected!")
        
        layout.separator()
        
        # Transfer settings
        layout.prop(self, "transfer_mode")
        
        if self.transfer_mode == 'NEW_TRACKS':
            layout.prop(self, "track_prefix")
        
        layout.prop(self, "preserve_timing")
        layout.prop(self, "mute_new_tracks")


class AH_TransferShapeKeyNLA(bpy.types.Operator):
    """Transfer shape key NLA strips between mesh objects with safe positioning"""
    bl_idname = "anim.transfer_shapekey_nla_fixed"
    bl_label = "Transfer Shape Key NLA (Safe)"
    bl_description = "Copy shape key NLA strips from active mesh to selected meshes without affecting existing strips"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Same properties as armature transfer
    transfer_mode: bpy.props.EnumProperty(
        name="Transfer Mode",
        items=[
            ('NEW_TRACKS', "New Tracks Only", "Always create new tracks, never modify existing ones"),
            ('APPEND', "Append to Existing", "Add to existing tracks if they exist"),
            ('REPLACE', "Replace Tracks", "Replace tracks with same name"),
        ],
        default='NEW_TRACKS'
    )
    
    preserve_timing: bpy.props.BoolProperty(
        name="Preserve Source Timing",
        description="Keep original strip timing from source object",
        default=True
    )
    
    mute_new_tracks: bpy.props.BoolProperty(
        name="Mute New Tracks",
        description="Automatically mute the transferred tracks",
        default=True
    )
    
    track_prefix: bpy.props.StringProperty(
        name="Track Prefix",
        description="Prefix for new track names to avoid conflicts",
        default="Transferred_"
    )
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH' and
                context.active_object.data.shape_keys is not None and
                len(context.selected_objects) >= 2)
    
    def execute(self, context):
        source_mesh = context.active_object
        target_meshes = [obj for obj in context.selected_objects 
                        if obj != source_mesh and obj.type == 'MESH' and obj.data.shape_keys]
        
        if not target_meshes:
            self.report({'ERROR'}, "Select source (active) and target mesh objects with shape keys")
            return {'CANCELLED'}
        
        source_shape_keys = source_mesh.data.shape_keys
        if not source_shape_keys.animation_data or not source_shape_keys.animation_data.nla_tracks:
            self.report({'ERROR'}, "Source mesh has no shape key NLA tracks")
            return {'CANCELLED'}
        
        strips_copied = 0
        tracks_created = 0
        
        for target_mesh in target_meshes:
            target_shape_keys = target_mesh.data.shape_keys
            
            # Ensure target has animation data
            if not target_shape_keys.animation_data:
                target_shape_keys.animation_data_create()
            
            # Store existing tracks to avoid modifying them
            existing_tracks = list(target_shape_keys.animation_data.nla_tracks)
            
            # Copy each NLA track
            for source_track in source_shape_keys.animation_data.nla_tracks:
                target_track = None
                
                if self.transfer_mode == 'NEW_TRACKS':
                    # Always create new track with unique name
                    track_name = self.get_unique_track_name(target_shape_keys, source_track.name)
                    target_track = target_shape_keys.animation_data.nla_tracks.new()
                    target_track.name = track_name
                    tracks_created += 1
                    
                elif self.transfer_mode == 'APPEND':
                    # Look for existing track with same name
                    for existing_track in target_shape_keys.animation_data.nla_tracks:
                        if existing_track.name == source_track.name:
                            target_track = existing_track
                            break
                    
                    # Create new track if not found
                    if target_track is None:
                        target_track = target_shape_keys.animation_data.nla_tracks.new()
                        target_track.name = source_track.name
                        tracks_created += 1
                        
                elif self.transfer_mode == 'REPLACE':
                    # Remove existing track with same name
                    for existing_track in list(target_shape_keys.animation_data.nla_tracks):
                        if existing_track.name == source_track.name:
                            target_shape_keys.animation_data.nla_tracks.remove(existing_track)
                            break
                    
                    # Create new track
                    target_track = target_shape_keys.animation_data.nla_tracks.new()
                    target_track.name = source_track.name
                    tracks_created += 1
                
                # Copy track properties (only for new tracks)
                if target_track and target_track not in existing_tracks:
                    target_track.mute = self.mute_new_tracks
                    target_track.lock = source_track.lock
                    if hasattr(source_track, 'solo'):
                        target_track.solo = source_track.solo
                
                # Copy each strip in the track
                for source_strip in source_track.strips:
                    # Create action copy to avoid sharing references
                    if source_strip.action:
                        action_copy = source_strip.action.copy()
                        action_copy.name = f"{source_strip.action.name}_Copy"
                    else:
                        action_copy = None
                    
                    # Determine strip timing
                    if self.preserve_timing:
                        start_frame = source_strip.frame_start
                    else:
                        # Place after existing strips in target track
                        start_frame = self.get_next_available_frame(target_track)
                    
                    # Create new strip
                    target_strip = target_track.strips.new(
                        name=source_strip.name,
                        start=int(start_frame),
                        action=action_copy
                    )
                    
                    # Copy strip properties
                    target_strip.frame_end = source_strip.frame_end
                    target_strip.extrapolation = source_strip.extrapolation
                    target_strip.blend_type = source_strip.blend_type
                    target_strip.influence = source_strip.influence
                    target_strip.mute = source_strip.mute
                    target_strip.use_reverse = source_strip.use_reverse
                    
                    # Copy blend settings
                    target_strip.blend_in = source_strip.blend_in
                    target_strip.blend_out = source_strip.blend_out
                    
                    strips_copied += 1
        
        self.report({'INFO'}, f"Created {tracks_created} tracks, copied {strips_copied} shape key strips to {len(target_meshes)} meshes")
        return {'FINISHED'}
    
    def get_unique_track_name(self, shape_keys, base_name):
        """Generate unique track name to avoid conflicts"""
        existing_names = {track.name for track in shape_keys.animation_data.nla_tracks}
        
        # Try with prefix first
        prefixed_name = f"{self.track_prefix}{base_name}"
        if prefixed_name not in existing_names:
            return prefixed_name
        
        # Add number suffix if needed
        counter = 1
        while f"{prefixed_name}_{counter:03d}" in existing_names:
            counter += 1
        
        return f"{prefixed_name}_{counter:03d}"
    
    def get_next_available_frame(self, track):
        """Find the next available frame after existing strips"""
        if not track.strips:
            return 1
        
        latest_end = max(strip.frame_end for strip in track.strips)
        return int(latest_end) + 10  # 10 frame gap
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def draw(self, context):
        layout = self.layout
        
        # Show selected objects
        source = context.active_object
        targets = [obj for obj in context.selected_objects 
                  if obj != source and obj.type == 'MESH' and obj.data.shape_keys]
        
        box = layout.box()
        box.label(text="Transfer Setup:", icon='SHAPEKEY_DATA')
        col = box.column(align=True)
        col.scale_y = 0.8
        
        if source:
            col.label(text=f"Source: {source.name}")
            if (source.data.shape_keys and 
                source.data.shape_keys.animation_data and 
                source.data.shape_keys.animation_data.nla_tracks):
                track_count = len(source.data.shape_keys.animation_data.nla_tracks)
                col.label(text=f"  • {track_count} shape key NLA tracks")
        
        if targets:
            col.label(text=f"Targets: {', '.join([obj.name for obj in targets])}")
        else:
            col.alert = True
            col.label(text="No target meshes with shape keys selected!")
        
        layout.separator()
        
        # Transfer settings
        layout.prop(self, "transfer_mode")
        
        if self.transfer_mode == 'NEW_TRACKS':
            layout.prop(self, "track_prefix")
        
        layout.prop(self, "preserve_timing")
        layout.prop(self, "mute_new_tracks")
        
class AH_CleanupAppendedCharacter(bpy.types.Operator):
    """Remove appended character after transferring NLA data"""
    bl_idname = "object.cleanup_appended_character"
    bl_label = "Cleanup Appended Character"
    bl_description = "Remove the appended character and its children after NLA transfer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not context.active_object:
            self.report({'ERROR'}, "No active object selected")
            return {'CANCELLED'}
        
        # Get the armature and all its children
        armature = context.active_object
        objects_to_delete = [armature]
        
        # Recursively collect all children
        def collect_children(obj):
            for child in obj.children:
                objects_to_delete.append(child)
                collect_children(child)
        
        collect_children(armature)
        
        # Delete all collected objects
        for obj in objects_to_delete:
            bpy.data.objects.remove(obj, do_unlink=True)
        
        self.report({'INFO'}, f"Removed {len(objects_to_delete)} objects")
        return {'FINISHED'}