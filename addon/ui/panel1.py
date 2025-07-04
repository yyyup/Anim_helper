import bpy
import bpy.props

# Import operators with standardized naming
from ..operators.animation_bake import AH_AnimationBake
from ..operators.decimate_ratio_75 import AH_DecimateKeys
from ..operators.add_shoulder_lock import AH_ShoulderLock
from ..operators.Add_copyT_and_reverse import AH_CopyTransforms
from ..operators.Copy_rotation import AH_CopyRotation
from ..operators.Knot_offset import AH_KnotOffset
from ..operators.NLA_action import AH_DuplicateSelectedBonesAction
from ..operators.Knot import AH_Knot
from ..operators.AH_inside import AH_inside
from ..operators.AH_world import AH_world  
from ..operators.AH_Swap import ANIM_H_OT_swap_parent_child
from ..operators.empty_size import AH_OT_EmptySizeGrow
from ..operators.empty_size import AH_OT_EmptySizeShrink
from ..operators.Offset import AH_offset
from ..operators.offset_cleanup import AH_offset_cleanup
from..operators.BakeToBones import AH_BakeToBones

# Import icon utilities safely with fallback
try:
    from ..icons import get_icon_id
    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False
    def get_icon_id(name):
        return 0


class AH_AnimTools(bpy.types.Panel):
    """Root panel for animation tools"""
    bl_label = "Anim Tools"
    bl_idname = "AH_PT_AnimTools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'

    def draw(self, context):
        self.layout.label(text="Tools for animation workflow")

class AH_PT_SpaceSwitching(bpy.types.Panel):
    bl_label = "Space Switching"
    bl_idname = "AH_PT_SpaceSwitching"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    bl_parent_id = "AH_PT_AnimTools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        self.draw_space_switching_section(layout)

    def draw_space_switching_section(self, layout):
        """Draw the space switching tools section with original layout"""
        box = layout.box()
        box.label(text="Space Switching Tools")
        
        # Locators subsection
        box.label(text="Locators", icon='EMPTY_ARROWS')
        col = box.column(align=True)
        
        # Knot Constraint button
        row = col.row()
        if HAS_ICONS and get_icon_id("knot") != 0:
            row.operator(AH_Knot.bl_idname, icon='EMPTY_ARROWS', text="T Constraint")
        else:
            row.operator(AH_Knot.bl_idname, icon='EMPTY_ARROWS', text="Knot Constraint")
            
        # Copy Transforms button row
        row = col.row(align=True)
        row.operator(AH_CopyTransforms.bl_idname, icon='EMPTY_AXIS', text="T Constraint B") 
        row.operator(AH_offset.bl_idname, icon='AUTOMERGE_OFF', text="offset")
        row.operator(AH_CopyRotation.bl_idname, icon='DRIVER_ROTATIONAL_DIFFERENCE', text="Copy Rotation")
        
        box.separator()
        
        # Parent subsection
        box.label(text="Parent", icon='ORIENTATION_PARENT')
        row = box.row(align=True)
        row = box.row()
        row.operator(AH_inside.bl_idname, icon='ORIENTATION_PARENT', text="Inside")
        row.operator(AH_world.bl_idname, icon='WORLD', text="World")
        row.operator(ANIM_H_OT_swap_parent_child.bl_idname, icon='ARROW_LEFTRIGHT', text="swap")
        
        box.separator()
        
        # Bonus Tools subsection
        box.label(text="Bonus Tools", icon='TOOL_SETTINGS')
        row = box.row()
        row.operator(AH_offset_cleanup.bl_idname, icon='TRASH', text="cleanup")
        
        # Shoulder Lock button in Bonus Tools
        row = box.row()
        row.operator(AH_ShoulderLock.bl_idname, icon='CONSTRAINT_BONE', text="Shoulder Lock")
        
        row = box.row()
        row.operator(AH_BakeToBones.bl_idname, icon='CONSTRAINT_BONE', text="bake to bones")
        
        box.separator()
        
        # Locator size subsection
        box.label(text="locator size")
        row = layout.row(align=True)       
        row.operator(AH_OT_EmptySizeGrow.bl_idname, icon='ADD', text="+")
        row.operator(AH_OT_EmptySizeShrink.bl_idname, icon='REMOVE', text="-")

class AH_PT_KeyframeCleanup(bpy.types.Panel):
    bl_label = "Keyframe Cleanup"
    bl_idname = "AH_PT_KeyframeCleanup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    bl_parent_id = "AH_PT_AnimTools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="Keyframe Cleanup")

        row = box.row()
        row.operator(AH_DecimateKeys.bl_idname, icon='COLORSET_02_VEC', text="Decimate Keyframes")

        row = box.row()
        row.prop(scene, "Factor", slider=True)
class AH_PT_AnimationBaking(bpy.types.Panel):
    bl_label = "Animation Baking"
    bl_idname = "AH_PT_AnimationBaking"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    bl_parent_id = "AH_PT_AnimTools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        bakeprops = context.scene.bprops

        box = layout.box()
        box.label(text="Animation Baking")

        row = box.row()
        row.alert = True
        row.operator(AH_AnimationBake.bl_idname, icon='REC', text="Easy Bake Animation")

        row = box.row()
        row.operator(AH_DuplicateSelectedBonesAction.bl_idname, icon='COLORSET_09_VEC', text="Duplicate Selected Bones Action")

        box.prop(bakeprops, "smart_bake", text="Smart Bake")

        if not bakeprops.smart_bake:
            row = box.row(align=True)
            row.prop(bakeprops, "custom_frame_start", text="Start")
            row.prop(bakeprops, "custom_frame_end", text="End")

        box.label(text="Keying Options:")
        col = box.column(align=True)
        col.prop(bakeprops, "visual_keying")
        col.prop(bakeprops, "only_selected_bones")

        box.label(text="Cleanup Options:")
        col = box.column(align=True)
        col.prop(bakeprops, "clear_constraints")
        col.prop(bakeprops, "clear_parents")
        col.prop(bakeprops, "overwrite_current_action")

class AH_PT_AnimToolsHelp(bpy.types.Panel):
    bl_label = "Help"
    bl_idname = "AH_PT_AnimToolsHelp"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    bl_parent_id = "AH_PT_AnimTools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Tips:")
        col = box.column(align=True)
        col.label(text="- Use Smart Bake for auto frame range")
        col.label(text="- Cleanup removes constraints after baking")
        col.label(text="- Change tab name in add-on prefs")

    def draw_header(self, context):
        """Draw panel header with icon"""
        layout = self.layout
        layout.label(icon='ARMATURE_DATA')


