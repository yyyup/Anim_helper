import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, IntProperty, StringProperty

class AH_NLA_DuplicateTrack(Operator):
    """Duplicate the entire NLA track (from active track or selected strip)."""
    bl_idname = "animhelper.nla_duplicate_track"
    bl_label = "Duplicate Track"
    bl_options = {'REGISTER', 'UNDO'}

    duplicate_actions: BoolProperty(
        name="Duplicate Actions",
        description="Create new Actions for each strip (independent copy)",
        default=True,
    )
    frame_offset: IntProperty(
        name="Frame Offset",
        description="Shift the duplicated track in time (frames)",
        default=0
    )
    name_suffix: StringProperty(
        name="Name Suffix",
        description="Suffix for new track/strips/actions",
        default=".dup"
    )

    # ---- helpers ----
    @staticmethod
    def _copy_common_strip_settings(src, dst):
        try:
            dst.action_frame_start = src.action_frame_start
            dst.action_frame_end   = src.action_frame_end
        except Exception:
            pass
        dst.repeat = src.repeat
        dst.scale  = src.scale
        dst.blend_type = src.blend_type
        dst.extrapolation = src.extrapolation
        dst.use_animated_influence = src.use_animated_influence
        dst.use_animated_time = src.use_animated_time
        dst.influence = src.influence
        dst.mute = src.mute
        try:
            dst.color = src.color
        except Exception:
            pass

    @staticmethod
    def _duplicate_action(src_action, suffix):
        new_action = src_action.copy()
        new_action.name = f"{src_action.name}{suffix}"
        new_action.use_fake_user = True
        return new_action

    @staticmethod
    def _find_track_of_strip(obj, strip):
        ad = getattr(obj, "animation_data", None)
        if not ad:
            return None
        for tr in ad.nla_tracks:
            for s in tr.strips:
                if s == strip:
                    return tr
        return None

    @classmethod
    def _resolve_source_track(cls, context, obj):
        ad = getattr(obj, "animation_data", None)
        if not ad or not ad.nla_tracks:
            raise RuntimeError("Active object has no NLA tracks.")

        active_track_ctx = getattr(context, "active_nla_track", None)
        if active_track_ctx:
            return active_track_ctx

        active_strip = getattr(context, "active_nla_strip", None)
        if active_strip:
            tr = cls._find_track_of_strip(obj, active_strip)
            if tr:
                return tr

        sel = list(getattr(context, "selected_nla_strips", []))
        if sel:
            tr = cls._find_track_of_strip(obj, sel[0])
            if tr:
                return tr

        if len(ad.nla_tracks) == 1:
            return ad.nla_tracks[0]

        raise RuntimeError("Select any strip in the track you want to duplicate (or make a track active).")

    @classmethod
    def _duplicate_track(cls, context, duplicate_actions=True, frame_offset=0, name_suffix=".dup"):
        obj = context.active_object
        if not obj:
            raise RuntimeError("No active object.")

        src_track = cls._resolve_source_track(context, obj)
        ad = obj.animation_data

        dst_track = ad.nla_tracks.new()
        dst_track.name = f"{src_track.name}{name_suffix}"
        dst_track.is_solo = src_track.is_solo
        dst_track.mute = src_track.mute
        dst_track.lock = False

        copied = 0
        skipped_meta = 0
        skipped_other = 0

        for s in sorted(src_track.strips, key=lambda x: x.frame_start):
            if s.type == 'CLIP' and s.action:
                action_to_use = cls._duplicate_action(s.action, name_suffix) if duplicate_actions else s.action
                new_start = s.frame_start + frame_offset

                # NlaTrack.strips.new requires int start; restore float afterward
                new_strip = dst_track.strips.new(f"{s.name}{name_suffix}", int(new_start), action_to_use)
                new_strip.frame_start = new_start
                new_strip.frame_end = new_strip.frame_start + (s.frame_end - s.frame_start)

                cls._copy_common_strip_settings(s, new_strip)
                copied += 1

            elif s.type == 'META':
                skipped_meta += 1
            else:
                skipped_other += 1

        return dst_track, copied, skipped_meta, skipped_other

    def execute(self, context):
        try:
            dst_track, copied, skipped_meta, skipped_other = self._duplicate_track(
                context,
                duplicate_actions=self.duplicate_actions,
                frame_offset=self.frame_offset,
                name_suffix=self.name_suffix
            )
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        msg = f"Created '{dst_track.name}': {copied} strip(s) copied"
        if skipped_meta:  msg += f", {skipped_meta} META skipped"
        if skipped_other: msg += f", {skipped_other} non-CLIP skipped"
        self.report({'INFO'}, msg)
        return {'FINISHED'}
