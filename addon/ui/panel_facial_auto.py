import bpy
from ..operators.Facial_auto_processor import AH_AutoProcessor, AH_StartAutoProcessing, AH_StopAutoProcessing, AH_AutoFacialProcessor, AH_ClearProcessedActions, AH_ToggleAutoCleanup, AH_SetLanguageSuffix

class AH_FacialAutoProcessingPanel(bpy.types.Panel):
    """Panel for auto-processing controls"""
    bl_label = "Facial Auto-Processing"
    bl_idname = "AH_PT_FacialAutoProcessing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    bl_order = 1  # Put at top of category
    
    def draw(self, context):
        layout = self.layout
        auto_proc = AH_AutoProcessor.get_instance()
        
        if auto_proc._is_running:
            # Show status when running
            box = layout.box()
            row = box.row()
            row.alert = True
            row.label(text="🔄 AUTO-PROCESSING ACTIVE", icon='PLAY')
            
            if auto_proc._rig:
                box.label(text=f"Monitoring: {auto_proc._rig.name}")
            box.label(text=f"Processed: {len(auto_proc._processed_actions)} animations")
            
            # Show current suffix
            if auto_proc._suffix:
                box.label(text=f"Language: {auto_proc._suffix}", icon='WORLD')
            else:
                box.label(text="Language: None", icon='WORLD')
            
            # Show cleanup status
            cleanup_status = "ON" if auto_proc._auto_cleanup else "OFF"
            cleanup_icon = 'CHECKMARK' if auto_proc._auto_cleanup else 'X'
            box.label(text=f"Auto-cleanup: {cleanup_status}", icon=cleanup_icon)
            
            # Show instructions
            col = box.column(align=True)
            col.label(text="Ready to process retargeted animations!")
            col.label(text="Just retarget your animations and they'll")
            col.label(text="be automatically organized.")
            
            layout.separator()
            
            # Control buttons
            col = layout.column(align=True)
            col.operator(AH_StopAutoProcessing.bl_idname, icon='PAUSE', text="Stop Auto-Processing")
            col.operator(AH_ClearProcessedActions.bl_idname, icon='X', text="Clear Processed List")
            
            # Settings section
            layout.separator()
            box = layout.box()
            box.label(text="Settings")
            
            # Language suffix setting (always available)
            row = box.row()
            row.operator(AH_SetLanguageSuffix.bl_idname, icon='WORLD', text="Set Language Suffix")
            
            row = box.row()
            cleanup_text = "Disable Auto-cleanup" if auto_proc._auto_cleanup else "Enable Auto-cleanup"
            cleanup_icon = 'CANCEL' if auto_proc._auto_cleanup else 'CHECKMARK'
            row.operator(AH_ToggleAutoCleanup.bl_idname, text=cleanup_text, icon=cleanup_icon)
            
        else:
            # Show start controls when not running
            box = layout.box()
            box.label(text="Facial Animation Auto-Processing", icon='FACE_MAPS')
            
            # Instructions
            col = box.column(align=True)
            col.label(text="Workflow:")
            col.label(text="1. Select your character rig")
            col.label(text="2. Set language suffix (optional)")
            col.label(text="3. Click 'Start Auto-Processing'")
            col.label(text="4. Retarget your animations")
            col.label(text="5. Actions auto-organize to NLA!")
            
            layout.separator()
            
            # Settings section
            box = layout.box()
            box.label(text="Settings")
            
            # Language suffix setting
            row = box.row()
            row.operator(AH_SetLanguageSuffix.bl_idname, icon='WORLD', text="Set Language Suffix")
            
            # Show current suffix status
            if auto_proc._suffix:
                row = box.row()
                row.label(text=f"Current: {auto_proc._suffix}", icon='CHECKMARK')
            else:
                row = box.row()
                row.label(text="Current: None", icon='BLANK1')
            
            # Auto-cleanup toggle
            row = box.row()
            cleanup_status = "Enabled" if auto_proc._auto_cleanup else "Disabled"
            cleanup_icon = 'CHECKMARK' if auto_proc._auto_cleanup else 'X'
            row.label(text=f"Auto-cleanup: {cleanup_status}", icon=cleanup_icon)
            
            row = box.row()
            cleanup_text = "Disable Auto-cleanup" if auto_proc._auto_cleanup else "Enable Auto-cleanup"
            cleanup_toggle_icon = 'CANCEL' if auto_proc._auto_cleanup else 'CHECKMARK'
            row.operator(AH_ToggleAutoCleanup.bl_idname, text=cleanup_text, icon=cleanup_toggle_icon)
            
            # Info about auto-cleanup
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="Auto-cleanup removes extra actions like:")
            col.label(text="• TearLine, Tongue, Eye animations")
            col.label(text="• Hat, Sword, Hair accessories")
            col.label(text="• Other empty/unnecessary retargeted actions")
            
            # Info about language suffixes
            layout.separator()
            box = layout.box()
            box.label(text="Language Suffixes", icon='WORLD')
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="Examples:")
            col.label(text="• FR for French → CC_JOH_RA_SPEECH_01_FR")
            col.label(text="• SP for Spanish → CC_JOH_SA_SPEECH_01_SP")
            col.label(text="• IT for Italian → CC_JOH_RA_SPEECH_01_IT")
            col.label(text="• Leave empty for no suffix")
            
            layout.separator()
            
            # Check if valid rig is selected
            valid_rig = (context.object and 
                        context.object.type == 'ARMATURE')
            
            if not valid_rig:
                row = layout.row()
                row.alert = True
                row.label(text="⚠️ Select an armature first", icon='ERROR')
            
            # Start button
            row = layout.row()
            row.scale_y = 1.5
            row.enabled = valid_rig
            row.operator(AH_StartAutoProcessing.bl_idname, icon='PLAY', text="Start Auto-Processing")
            
            # Manual processing option
            layout.separator()
            box = layout.box()
            box.label(text="Manual Processing")
            row = box.row()
            row.enabled = valid_rig
            row.operator(AH_AutoFacialProcessor.bl_idname, text="Process Current Animation", icon='IMPORT')