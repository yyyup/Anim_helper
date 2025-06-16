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
        
        # Check if we have selected objects with NLA data
        selected_info = self.get_selected_nla_info(context)
        
        # Head transition smoothing section
        box = layout.box()
        box.label(text="Facial Transition Smoothing", icon='SMOOTHCURVE')
        
        # Show selected objects info
        if selected_info['armatures'] or selected_info['meshes']:
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="Selected objects:")
            
            if selected_info['armatures']:
                col.label(text=f"  • {selected_info['armatures']} armature(s)")
            if selected_info['meshes']:
                col.label(text=f"  • {selected_info['meshes']} mesh(es) with shape keys")
            col.label(text=f"  • {selected_info['total_strips']} NLA strips total")
            
            box.separator()
            
            # Main fix button
            row = box.row()
            row.scale_y = 1.3
            row.operator(AH_NLASmoothTransitions.bl_idname, 
                        text="Smooth Selected Objects", 
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
            
            # Medium blending (5 frames)
            row = col.row()
            op = row.operator(AH_NLASmoothTransitions.bl_idname, 
                            text="Medium (5f)", 
                            icon='KEYTYPE_BREAKDOWN_VEC')
            op.blend_frames = 5
            
            # Heavy blending (8 frames)
            row = col.row()
            op = row.operator(AH_NLASmoothTransitions.bl_idname, 
                            text="Heavy (8f)", 
                            icon='KEYTYPE_EXTREME_VEC')
            op.blend_frames = 8
            
            box.separator()
            
            # Clean up button
            row = box.row()
            row.alert = True
            row.operator(AH_NLACleanTransitions.bl_idname, 
                        text="Remove All Blending", 
                        icon='TRASH')
        
        else:
            # No valid selected objects
            col = box.column(align=True)
            col.scale_y = 0.9
            
            if not context.selected_objects:
                col.label(text="No objects selected", icon='ERROR')
                col.label(text="Select armatures or meshes with shape keys")
            else:
                # Show what's selected but not valid
                selected_types = set(obj.type for obj in context.selected_objects)
                col.label(text="Selected objects have no NLA data", icon='INFO')
                col.label(text=f"Selected types: {', '.join(selected_types)}")
                col.label(text="Need: Armatures or Meshes with shape keys")
        
        # Instructions section
        layout.separator()
        box = layout.box()
        box.label(text="💡 How to Use", icon='INFO')
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="1. Select character armature(s)")
        col.label(text="2. Or select mesh(es) with shape keys")
        col.label(text="3. Choose blending strength")
        col.label(text="4. Only selected objects are affected")
        col.label(text="• Start with 'Medium (5f)' for most cases")
        col.label(text="• Uses REPLACE mode for proper override")
    
    def get_selected_nla_info(self, context):
        """Get info about selected objects with NLA data"""
        info = {
            'armatures': 0,
            'meshes': 0,
            'total_strips': 0
        }
        
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                if (obj.animation_data and obj.animation_data.nla_tracks):
                    info['armatures'] += 1
                    # Count strips
                    for track in obj.animation_data.nla_tracks:
                        info['total_strips'] += len(track.strips)
            
            elif obj.type == 'MESH' and obj.data.shape_keys:
                if (obj.data.shape_keys.animation_data and 
                    obj.data.shape_keys.animation_data.nla_tracks):
                    info['meshes'] += 1
                    # Count strips
                    for track in obj.data.shape_keys.animation_data.nla_tracks:
                        info['total_strips'] += len(track.strips)
        
        return info
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='SMOOTHCURVE')