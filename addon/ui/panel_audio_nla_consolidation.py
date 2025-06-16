import bpy
from ..operators.Audio_NLA_consolidation import AH_ConsolidateAudioNLA

class AH_AudioNLAConsolidationPanel(bpy.types.Panel):
    """Audio-NLA Consolidation panel"""
    bl_label = "Audio-NLA Consolidation"
    bl_idname = "AH_PT_AudioNLAConsolidation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="🎵 Audio-NLA Consolidation", icon='NLA')
        
        # Show scene info
        seq_editor = context.scene.sequence_editor
        audio_count = len([s for s in seq_editor.sequences if s.type == 'SOUND']) if seq_editor else 0
        
        nla_info = self.get_nla_info(context)
        
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text=f"Audio strips: {audio_count}")
        col.label(text=f"NLA tracks: {nla_info['total_tracks']}")
        col.label(text=f"NLA strips: {nla_info['total_strips']}")
        
        if audio_count == 0:
            col.label(text="⚠️ No audio found", icon='ERROR')
        if nla_info['total_strips'] == 0:
            col.label(text="⚠️ No NLA strips found", icon='ERROR')
        
        if nla_info['total_tracks'] > 1:
            col.label(text="✅ Multiple tracks - consolidation ready", icon='CHECKMARK')
        
        box.separator()
        
        # Main operator button
        enabled = audio_count > 0 and nla_info['total_strips'] > 0
        
        row = box.row()
        row.scale_y = 1.3
        row.enabled = enabled
        row.operator(AH_ConsolidateAudioNLA.bl_idname, 
                    text="Consolidate Audio-NLA", 
                    icon='NLA')
        
        if enabled:
            box.separator()
            
            # Quick presets
            col = box.column(align=True)
            col.label(text="Quick Actions:")
            
            # Standard consolidation (NLA to audio)
            row = col.row()
            op = row.operator(AH_ConsolidateAudioNLA.bl_idname, 
                            text="Consolidate (Keep Audio)", 
                            icon='SOUND')
            op.target_mode = 'ACTIVE_OBJECT'
            op.alignment_mode = 'MOVE_NLA_TO_AUDIO'
            op.use_audio_filter = False
            op.remove_original_tracks = True
            
            # With audio keyword filter
            row = col.row()
            op = row.operator(AH_ConsolidateAudioNLA.bl_idname, 
                            text="Consolidate with Filter", 
                            icon='FILTER')
            op.target_mode = 'ACTIVE_OBJECT'
            op.alignment_mode = 'MOVE_NLA_TO_AUDIO'
            op.use_audio_filter = True
            op.audio_keyword_filter = ""  # User will fill this in dialog
            op.remove_original_tracks = True
        
        # Show current active object info
        if context.active_object:
            active = context.active_object
            if active.type == 'ARMATURE':
                box.separator()
                col = box.column(align=True)
                col.scale_y = 0.8
                col.label(text=f"Active: {active.name} (Armature)")
                
                # Show child meshes with shape keys
                shape_meshes = [child for child in active.children 
                              if child.type == 'MESH' and child.data.shape_keys]
                if shape_meshes:
                    col.label(text=f"Shape key meshes: {len(shape_meshes)}")
        
        # Tips section
        layout.separator()
        box = layout.box()
        box.label(text="💡 Usage Tips", icon='INFO')
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="• Use 'Keep Audio' to preserve audio timing")
        col.label(text="• Use keyword filter for specific characters")
        col.label(text="• Works with active object + children (safest)")
        col.label(text="• Consolidates multiple tracks into one")
    
    def get_nla_info(self, context):
        """Get summary of NLA data in scene"""
        info = {
            'total_tracks': 0,
            'total_strips': 0
        }
        
        # Count armature tracks and strips
        for obj in context.scene.objects:
            if (obj.type == 'ARMATURE' and 
                obj.animation_data and 
                obj.animation_data.nla_tracks):
                track_count = len(obj.animation_data.nla_tracks)
                info['total_tracks'] += track_count
                
                for track in obj.animation_data.nla_tracks:
                    info['total_strips'] += len(track.strips)
        
        # Count shape key tracks and strips
        for obj in context.scene.objects:
            if (obj.type == 'MESH' and 
                obj.data.shape_keys and
                obj.data.shape_keys.animation_data and
                obj.data.shape_keys.animation_data.nla_tracks):
                track_count = len(obj.data.shape_keys.animation_data.nla_tracks)
                info['total_tracks'] += track_count
                
                for track in obj.data.shape_keys.animation_data.nla_tracks:
                    info['total_strips'] += len(track.strips)
        
        return info
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='NLA')