import bpy
import bpy.props

# Import operators with standardized naming
from ..operators.animation_bake import AH_AnimationBake
from ..operators.decimate_ratio_75 import AH_DecimateKeys
from ..operators.add_shoulder_lock import AH_ShoulderLock
from ..operators.Add_copyT_and_reverse import AH_CopyTransforms
from ..operators.NLA_action import AH_DuplicateSelectedBonesAction
from ..operators.Knot import AH_Knot

# Import icon utilities
from ..icons import get_icon_id

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
        
        # Space switching tools section
        box = layout.box()
        box.label(text="Space Switching Tools")
        
        # Custom icon for Knot operator
        row = box.row()
        row.operator(AH_Knot.bl_idname, icon_value=get_icon_id("knot"), text="Knot Constraint")
        
        # Color 2 - Green themed button
        row = box.row()
        row.operator(AH_ShoulderLock.bl_idname, icon='COLORSET_03_VEC', text="Shoulder Lock")
        
        # Color 3 - Purple themed button
        row = box.row()
        row.operator(AH_CopyTransforms.bl_idname, icon='COLORSET_04_VEC', text="Copy Transforms")
        
        layout.separator()
        
        # Keyframe cleanup section
        box = layout.box()
        box.label(text="Keyframe Cleanup")
        
        # Color 4 - Orange themed button for decimation
        row = box.row()
        row.operator(AH_DecimateKeys.bl_idname, icon='COLORSET_02_VEC', text="Decimate Keyframes")
        
        # Slider with better formatting
        row = box.row()
        row.prop(scene, "Factor", slider=True)
        
        layout.separator()
        
        # Animation baking section
        box = layout.box()
        box.label(text="Animation Baking")
        
        # Color 5 - Red themed button for recording/baking
        row = box.row()
        row.alert = True  # This makes the button reddish (alert style)
        row.operator(AH_AnimationBake.bl_idname, icon='REC', text="Easy Bake Animation")
        
        # Yellow themed button for NLA
        row = box.row()
        row.operator(AH_DuplicateSelectedBonesAction.bl_idname, icon='COLORSET_09_VEC', text="Duplicate Selected Bones Action")
        
        # Baking options in a sub-box with different background
        sub_box = box.box()
        sub_box.label(text="Baking Options", icon='PREFERENCES')
        
        # Smart bake option
        sub_box.prop(bakeprops, "smart_bake")
        
        if not bakeprops.smart_bake:
            row = sub_box.row(align=True)
            row.prop(bakeprops, "custom_frame_start", text="Start")
            row.prop(bakeprops, "custom_frame_end", text="End")
        
        # Options in columns for cleaner layout
        col1 = sub_box.column(align=True)
        col1.label(text="Keying Options:")
        col1.prop(bakeprops, "visual_keying")
        col1.prop(bakeprops, "only_selected_bones")
        
        col2 = sub_box.column(align=True)
        col2.label(text="Cleanup Options:")
        col2.prop(bakeprops, "clear_constraints")
        col2.prop(bakeprops, "clear_parents")
        col2.prop(bakeprops, "overwrite_current_action")

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='ARMATURE_DATA')