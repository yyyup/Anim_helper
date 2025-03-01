import bpy

class Anim_H_SnapPlayhead_to_audio(bpy.types.Operator):
    """Snaps the playhead to the selected audio or NLA strip"""
    bl_idname = "animation.snap_playhead_to_strip"
    bl_label = "Snap Playhead to Strip"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_strip = None
        
        # Check for selected audio strip
        for strip in bpy.context.scene.sequence_editor.sequences_all:
            if strip.type == 'SOUND' and strip.select:
                selected_strip = strip
                break
        
        # Check for selected NLA strip if no audio strip is selected
        if not selected_strip:
            if bpy.context.object.animation_data and bpy.context.object.animation_data.nla_tracks:
                for track in bpy.context.object.animation_data.nla_tracks:
                    for strip in track.strips:
                        if strip.select:
                            selected_strip = strip
                            break
                    if selected_strip:
                        break
        
        if selected_strip:
            # Snap the playhead to the start frame of the selected strip (convert to int)
            bpy.context.scene.frame_current = int(selected_strip.frame_start)
            self.report({'INFO'}, f"Snapped playhead to frame {int(selected_strip.frame_start)}")
        else:
            self.report({'WARNING'}, "No strip selected.")
        
        return {'FINISHED'}