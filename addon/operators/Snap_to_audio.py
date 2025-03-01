import bpy

class AH_SnapPlayheadToStrip(bpy.types.Operator):
    """Snap the playhead to the selected audio or NLA strip for easier animation syncing"""
    bl_idname = "animation.snap_playhead_to_strip"
    bl_label = "Snap Playhead to Strip"
    bl_description = "Snap the playhead to the beginning of selected audio or NLA strip"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_strip = None
        
        # First check for selected audio strip in the sequencer
        if context.scene.sequence_editor and context.scene.sequence_editor.sequences_all:
            for strip in context.scene.sequence_editor.sequences_all:
                if strip.type == 'SOUND' and strip.select:
                    selected_strip = strip
                    break
        
        # If no audio strip is found, check for selected NLA strip
        if not selected_strip and context.object and context.object.animation_data:
            if context.object.animation_data.nla_tracks:
                for track in context.object.animation_data.nla_tracks:
                    for strip in track.strips:
                        if strip.select:
                            selected_strip = strip
                            break
                    if selected_strip:
                        break
        
        if selected_strip:
            # Snap the playhead to the start frame of the selected strip
            context.scene.frame_current = int(selected_strip.frame_start)
            self.report({'INFO'}, f"Snapped playhead to frame {int(selected_strip.frame_start)}")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No audio or NLA strip selected. Select a strip in the Sequencer or NLA editor.")
            return {'CANCELLED'}