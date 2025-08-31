import bpy
from bpy.types import Panel

class AH_PT_NLA_AnimHelper(Panel):
    bl_label = "AnimHelper · NLA"
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'AnimHelper'

    @classmethod
    def poll(cls, context):
        # Show whenever we’re in the NLA editor
        return (context.area and context.area.type == 'NLA_EDITOR')

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Duplicate Track")

        col.operator("animhelper.nla_duplicate_track",
                     text="Duplicate Track",
                     icon="DUPLICATE")

        op = col.operator("animhelper.nla_duplicate_track",
                          text="Duplicate (Keep Same Actions)",
                          icon="DUPLICATE")
        op.duplicate_actions = False
        op.frame_offset = 0
        op.name_suffix = ".dup"

        # Advanced (from Scene props)
        p = getattr(context.scene, "ah_nla", None)
        box = layout.box()
        box.label(text="Advanced")

        if p is None:
            box.label(text="ah_nla props not registered.", icon="ERROR")
            return

        row = box.row(align=True); row.prop(p, "duplicate_actions")
        row = box.row(align=True); row.prop(p, "frame_offset")
        row = box.row(align=True); row.prop(p, "name_suffix")

        run = box.operator("animhelper.nla_duplicate_track",
                           text="Run with Advanced Settings",
                           icon="PLAY")
        run.duplicate_actions = p.duplicate_actions
        run.frame_offset      = p.frame_offset
        run.name_suffix       = p.name_suffix
