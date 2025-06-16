import bpy

class AH_TransferNLAStrips(bpy.types.Operator):
    """Transfer NLA strips from source object to target object with smart options"""
    bl_idname = "anim.transfer_nla_strips"
    bl_label = "Transfer NLA Strips"
    bl_description = "Copy NLA strips from active object to selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Properties for different transfer modes
    transfer_mode: bpy.props.EnumProperty(
        name="Transfer Mode",
        items=[
            ('APPEND', "Append", "Add new tracks to existing ones"),
            ('REPLACE', "Replace", "Replace all existing NLA tracks"),
            ('MERGE', "Merge", "Merge with tracks of same name")
        ],
        default='APPEND'
    )
    
    mute_new_tracks: bpy.props.BoolProperty(
        name="Mute New Tracks",
        description="Automatically mute the transferred tracks",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.animation_data is not None and
                len(context.selected_objects) >= 2)
    
    def execute(self, context):
        source_obj = context.active_object
        target_objects = [obj for obj in context.selected_objects if obj != source_obj]
        
        if not target_objects:
            self.report({'ERROR'}, "Select at least one target object")
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
            
            # Handle different transfer modes
            if self.transfer_mode == 'REPLACE':
                # Clear existing tracks
                for track in list(target_obj.animation_data.nla_tracks):
                    target_obj.animation_data.nla_tracks.remove(track)
            
            # Copy each NLA track from source to target
            for source_track in source_obj.animation_data.nla_tracks:
                track_name = source_track.name
                
                target_track = None
                
                # Handle merge mode
                if self.transfer_mode == 'MERGE':
                    # Look for existing track with same name
                    for existing_track in target_obj.animation_data.nla_tracks:
                        if existing_track.name == track_name:
                            target_track = existing_track
                            break
                
                # Create new track if needed
                if target_track is None:
                    target_track = target_obj.animation_data.nla_tracks.new()
                    target_track.name = track_name
                    tracks_created += 1
                
                # Copy track properties
                target_track.mute = self.mute_new_tracks if self.mute_new_tracks else source_track.mute
                target_track.lock = source_track.lock
                if hasattr(source_track, 'solo'):
                    target_track.solo = source_track.solo
                
                # Copy each strip in the track
                for source_strip in source_track.strips:
                    # Check if strip already exists in merge mode
                    strip_exists = False
                    if self.transfer_mode == 'MERGE':
                        for existing_strip in target_track.strips:
                            if (existing_strip.name == source_strip.name and 
                                abs(existing_strip.frame_start - source_strip.frame_start) < 1):
                                strip_exists = True
                                break
                    
                    if not strip_exists:
                        target_strip = target_track.strips.new(
                            name=source_strip.name,
                            start=int(source_strip.frame_start),
                            action=source_strip.action
                        )
                        
                        # Copy strip properties
                        target_strip.frame_end = source_strip.frame_end
                        target_strip.extrapolation = source_strip.extrapolation
                        target_strip.blend_type = source_strip.blend_type
                        target_strip.influence = source_strip.influence
                        target_strip.mute = source_strip.mute
                        target_strip.use_reverse = source_strip.use_reverse
                        
                        strips_copied += 1
        
        self.report({'INFO'}, f"Created {tracks_created} tracks, copied {strips_copied} strips to {len(target_objects)} objects")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AH_TransferShapeKeyNLA(bpy.types.Operator):
    """Transfer shape key NLA strips between mesh objects with smart options"""
    bl_idname = "anim.transfer_shapekey_nla"
    bl_label = "Transfer Shape Key NLA"
    bl_description = "Copy shape key NLA strips from active mesh to selected meshes"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Same properties as armature transfer
    transfer_mode: bpy.props.EnumProperty(
        name="Transfer Mode",
        items=[
            ('APPEND', "Append", "Add new tracks to existing ones"),
            ('REPLACE', "Replace", "Replace all existing NLA tracks"),
            ('MERGE', "Merge", "Merge with tracks of same name")
        ],
        default='APPEND'
    )
    
    mute_new_tracks: bpy.props.BoolProperty(
        name="Mute New Tracks",
        description="Automatically mute the transferred tracks",
        default=True
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
                        if obj != source_mesh and obj.type == 'MESH']
        
        if not target_meshes:
            self.report({'ERROR'}, "Select at least one target mesh object")
            return {'CANCELLED'}
        
        source_shape_keys = source_mesh.data.shape_keys
        if not source_shape_keys.animation_data or not source_shape_keys.animation_data.nla_tracks:
            self.report({'ERROR'}, "Source mesh has no shape key NLA tracks")
            return {'CANCELLED'}
        
        strips_copied = 0
        tracks_created = 0
        
        for target_mesh in target_meshes:
            if not target_mesh.data.shape_keys:
                self.report({'WARNING'}, f"{target_mesh.name} has no shape keys, skipping")
                continue
            
            target_shape_keys = target_mesh.data.shape_keys
            
            # Ensure target has animation data
            if not target_shape_keys.animation_data:
                target_shape_keys.animation_data_create()
            
            # Handle different transfer modes
            if self.transfer_mode == 'REPLACE':
                for track in list(target_shape_keys.animation_data.nla_tracks):
                    target_shape_keys.animation_data.nla_tracks.remove(track)
            
            # Copy each NLA track
            for source_track in source_shape_keys.animation_data.nla_tracks:
                track_name = source_track.name
                
                target_track = None
                
                if self.transfer_mode == 'MERGE':
                    for existing_track in target_shape_keys.animation_data.nla_tracks:
                        if existing_track.name == track_name:
                            target_track = existing_track
                            break
                
                if target_track is None:
                    target_track = target_shape_keys.animation_data.nla_tracks.new()
                    target_track.name = track_name
                    tracks_created += 1
                
                target_track.mute = self.mute_new_tracks if self.mute_new_tracks else source_track.mute
                target_track.lock = source_track.lock
                if hasattr(source_track, 'solo'):
                    target_track.solo = source_track.solo
                
                # Copy each strip in the track
                for source_strip in source_track.strips:
                    strip_exists = False
                    if self.transfer_mode == 'MERGE':
                        for existing_strip in target_track.strips:
                            if (existing_strip.name == source_strip.name and 
                                abs(existing_strip.frame_start - source_strip.frame_start) < 1):
                                strip_exists = True
                                break
                    
                    if not strip_exists:
                        target_strip = target_track.strips.new(
                            name=source_strip.name,
                            start=int(source_strip.frame_start),
                            action=source_strip.action
                        )
                        
                        # Copy strip properties
                        target_strip.frame_end = source_strip.frame_end
                        target_strip.extrapolation = source_strip.extrapolation
                        target_strip.blend_type = source_strip.blend_type
                        target_strip.influence = source_strip.influence
                        target_strip.mute = source_strip.mute
                        target_strip.use_reverse = source_strip.use_reverse
                        
                        strips_copied += 1
        
        self.report({'INFO'}, f"Created {tracks_created} tracks, copied {strips_copied} shape key strips to {len(target_meshes)} meshes")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


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