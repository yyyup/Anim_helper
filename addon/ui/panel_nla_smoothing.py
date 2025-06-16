import bpy
from ..operators.NLA_smoothing import AH_NLASmoothTransitions, AH_NLACleanTransitions

class AH_NLASmoothingPanel(bpy.types.Panel):
    """NLA Smoothing Tools panel"""
    bl_label = "NLA Smoothing"
    bl_idname = "AH_PT_NLASmoothing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        
        # Check if we have NLA data
        has_nla = self.check_nla_data(context)
        
        # Head transition smoothing section
        box = layout.box()
        box.label(text="Facial Transition Smoothing", icon='SMOOTHCURVE')
        
        if has_nla:
            # Instructions
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="Fix head/face popping between")
            col.label(text="facial animation strips:")
            
            box.separator()
            
            # Main fix button
            row = box.row()
            row.scale_y = 1.3
            row.operator(AH_NLASmoothTransitions.bl_idname, 
                        text="Smooth Transitions", 
                        icon='SMOOTHCURVE')
            
            box.separator()
            
            # Quick presets
            col = box.column(align=True)
            col.label(text="Quick Presets:")
            
            # Light blending (3 frames)
            row = col.row()
            op = row.operator(AH_NLASmoothTransitions.bl_idname, 
                            text="Light (3f)", 
                            icon='KEYTYPE_KEYFRAME_VEC')
            op.blend_frames = 3
            op.process_all_tracks = True
            
            # Medium blending (5 frames)
            row = col.row()
            op = row.operator(AH_NLASmoothTransitions.bl_idname, 
                            text="Medium (5f)", 
                            icon='KEYTYPE_BREAKDOWN_VEC')
            op.blend_frames = 5
            op.process_all_tracks = True
            
            # Heavy blending (8 frames)
            row = col.row()
            op = row.operator(AH_NLASmoothTransitions.bl_idname, 
                            text="Heavy (8f)", 
                            icon='KEYTYPE_EXTREME_VEC')
            op.blend_frames = 8
            op.process_all_tracks = True
            
            box.separator()
            
            # Clean up button
            row = box.row()
            row.alert = True
            row.operator(AH_NLACleanTransitions.bl_idname, 
                        text="Remove All Blending", 
                        icon='TRASH')
            
            # Show NLA info
            nla_info = self.get_nla_info(context)
            if nla_info['total_tracks'] > 0:
                box.separator()
                col = box.column(align=True)
                col.scale_y = 0.8
                col.label(text=f"Found: {nla_info['armature_tracks']} armature tracks")
                col.label(text=f"       {nla_info['shapekey_tracks']} shape key tracks")
                col.label(text=f"       {nla_info['total_strips']} total strips")
        
        else:
            # No NLA data available
            col = box.column(align=True)
            col.scale_y = 0.9
            if not context.active_object:
                col.label(text="No object selected", icon='ERROR')
            elif not self.has_any_nla_tracks(context):
                col.label(text="No NLA tracks found", icon='ERROR')
                col.label(text="Process facial animations first")
            else:
                col.label(text="Select object with NLA tracks", icon='INFO')
        
        # Tips section
        layout.separator()
        box = layout.box()
        box.label(text="💡 Usage Tips", icon='INFO')
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="• Start with 'Medium (5f)' for most cases")
        col.label(text="• Use 'Light (3f)' for subtle transitions")
        col.label(text="• Use 'Heavy (8f)' for dramatic smoothing")
        col.label(text="• Works on both bones and shape keys")
        col.label(text="• Uses REPLACE mode for proper override")
    
    def check_nla_data(self, context):
        """Check if scene has usable NLA data"""
        if not context.active_object:
            return False
        
        # Check for armature NLA
        if context.active_object.type == 'ARMATURE':
            if (context.active_object.animation_data and 
                context.active_object.animation_data.nla_tracks):
                return True
        
        # Check for any NLA data in scene
        return self.has_any_nla_tracks(context)
    
    def has_any_nla_tracks(self, context):
        """Check if any object in scene has NLA tracks"""
        for obj in context.scene.objects:
            # Check armatures
            if (obj.type == 'ARMATURE' and 
                obj.animation_data and 
                obj.animation_data.nla_tracks):
                return True
            
            # Check shape keys
            if (obj.type == 'MESH' and 
                obj.data.shape_keys and 
                obj.data.shape_keys.animation_data and
                obj.data.shape_keys.animation_data.nla_tracks):
                return True
        
        return False
    
    def get_nla_info(self, context):
        """Get summary of NLA data in scene"""
        info = {
            'armature_tracks': 0,
            'shapekey_tracks': 0,
            'total_tracks': 0,
            'total_strips': 0
        }
        
        for obj in context.scene.objects:
            # Count armature tracks
            if (obj.type == 'ARMATURE' and 
                obj.animation_data and 
                obj.animation_data.nla_tracks):
                track_count = len(obj.animation_data.nla_tracks)
                info['armature_tracks'] += track_count
                info['total_tracks'] += track_count
                
                for track in obj.animation_data.nla_tracks:
                    info['total_strips'] += len(track.strips)
            
            # Count shape key tracks
            if (obj.type == 'MESH' and 
                obj.data.shape_keys and 
                obj.data.shape_keys.animation_data and
                obj.data.shape_keys.animation_data.nla_tracks):
                track_count = len(obj.data.shape_keys.animation_data.nla_tracks)
                info['shapekey_tracks'] += track_count
                info['total_tracks'] += track_count
                
                for track in obj.data.shape_keys.animation_data.nla_tracks:
                    info['total_strips'] += len(track.strips)
        
        return info
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='SMOOTHCURVE')