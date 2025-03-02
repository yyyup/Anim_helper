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

# Import icon utilities safely with fallback
try:
    from ..icons import get_icon_id
    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False
    def get_icon_id(name):
        return 0

class AH_AnimTools(bpy.types.Panel):
    """Animation tools panel in the 3D View sidebar"""
    bl_label = "Anim Tools"
    bl_idname = "AH_PT_AnimTools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bakeprops = scene.bprops
        
        # Reverse Hierarchy section (previously Space Switching Tools)
        box = layout.box()
        box.label(text="Reverse Hierarchy")
        
        # Create a grid layout for the buttons in Reverse Hierarchy
        grid = box.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=True, align=True)
        
        # Knot Constraint button
        row = grid.row()
        if HAS_ICONS and get_icon_id("knot") != 0:
            row.operator(AH_Knot.bl_idname, icon_value=get_icon_id("knot"), text="Knot Constraint")
        else:
            row.operator(AH_Knot.bl_idname, icon='COLORSET_01_VEC', text="Knot Constraint")
        
        # New Knot Offset button
        row = grid.row()
        row.operator("object.create_constrained_empties", icon='COLORSET_05_VEC', text="Knot Offset")
        
        # Copy Transforms button  
        row = grid.row()
        row.operator(AH_CopyTransforms.bl_idname, icon='COLORSET_04_VEC', text="Copy Transforms")
        
        # Copy Rotation button
        row = grid.row()
        row.operator(AH_CopyRotation.bl_idname, icon='COLORSET_06_VEC', text="Copy Rotation")
        
        # Bonus Tools section
        box = layout.box()
        box.label(text="Bonus Tools")
        
        # Shoulder Lock button in Bonus Tools
        row = box.row()
        row.operator(AH_ShoulderLock.bl_idname, icon='COLORSET_03_VEC', text="Shoulder Lock")
        
        layout.separator()
        
        # Keyframe cleanup section
        box = layout.box()
        box.label(text="Keyframe Cleanup")
        
        # Decimate Keyframes button
        row = box.row()
        row.operator(AH_DecimateKeys.bl_idname, icon='COLORSET_02_VEC', text="Decimate Keyframes")
        
        # Decimate Factor slider
        row = box.row()
        row.prop(scene, "Factor", slider=True)
        
        layout.separator()
        
        # Animation baking section
        box = layout.box()
        box.label(text="Animation Baking")
        
        # Easy Bake Animation button (in alert/red style)
        row = box.row()
        row.alert = True
        row.operator(AH_AnimationBake.bl_idname, icon='REC', text="Easy Bake Animation")
        
        # Duplicate Selected Bones Action button
        row = box.row()
        row.operator(AH_DuplicateSelectedBonesAction.bl_idname, icon='COLORSET_09_VEC', text="Duplicate Selected Bones Action")
        
        # Baking Options section (collapsible)
        box.prop(bakeprops, "smart_bake", text="Smart Bake")
        
        if not bakeprops.smart_bake:
            row = box.row(align=True)
            row.prop(bakeprops, "custom_frame_start", text="Start")
            row.prop(bakeprops, "custom_frame_end", text="End")
        
        # Keying Options subsection
        box.label(text="Keying Options:")
        col = box.column(align=True)
        col.prop(bakeprops, "visual_keying")
        col.prop(bakeprops, "only_selected_bones")
        
        # Cleanup Options subsection
        box.label(text="Cleanup Options:")
        col = box.column(align=True)
        col.prop(bakeprops, "clear_constraints")
        col.prop(bakeprops, "clear_parents")
        col.prop(bakeprops, "overwrite_current_action")

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='ARMATURE_DATA')