import bpy

# Import operators
from ..operators.NLA_transfer import AH_TransferNLAStrips, AH_TransferShapeKeyNLA, AH_CleanupAppendedCharacter


class AH_NLATransferPanel(bpy.types.Panel):
    """NLA Transfer Tools panel"""
    bl_label = "NLA Transfer Tools"
    bl_idname = "AH_PT_NLATransfer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        
        # NLA Transfer workflow section
        box = layout.box()
        box.label(text="NLA Transfer Workflow", icon='IMPORT')
        
        # Instructions
        col = box.column(align=True)
        col.label(text="1. Append processed character")
        col.label(text="2. Select target → source")
        col.label(text="3. Transfer NLA strips")
        col.label(text="4. Cleanup appended character")
        
        box.separator()
        
        # Transfer buttons
        col = box.column(align=True)
        
        # NLA Transfer button
        row = col.row()
        row.operator(AH_TransferNLAStrips.bl_idname, 
                    text="Transfer Armature NLA", 
                    icon='NLA')
        
        # Shape Key NLA Transfer button  
        row = col.row()
        row.operator(AH_TransferShapeKeyNLA.bl_idname, 
                    text="Transfer Shape Key NLA", 
                    icon='SHAPEKEY_DATA')
        
        box.separator()
        
        # Cleanup button (styled as destructive action)
        row = box.row()
        row.alert = True
        row.operator(AH_CleanupAppendedCharacter.bl_idname, 
                    text="Cleanup Appended Character", 
                    icon='TRASH')
        
        # Selection info
        if context.selected_objects:
            box.separator()
            box.label(text=f"Selected: {len(context.selected_objects)} objects")
            if context.active_object:
                box.label(text=f"Active: {context.active_object.name}")
                # Show if object has NLA tracks
                if (context.active_object.animation_data and 
                    context.active_object.animation_data.nla_tracks):
                    track_count = len(context.active_object.animation_data.nla_tracks)
                    box.label(text=f"NLA Tracks: {track_count}", icon='NLA')
        else:
            box.separator()
            box.label(text="No objects selected", icon='ERROR')
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='NLA')