import bpy
import bpy.props

# Import operators with standardized naming
from ..operators.animation_bake import AH_AnimationBake
from ..operators.decimate_ratio_75 import AH_DecimateKeys
from ..operators.add_shoulder_lock import AH_ShoulderLock
from ..operators.Add_copyT_and_reverse import AH_CopyTransforms
from ..operators.Copy_rotation import AH_CopyRotation
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
        
        # Space switching tools section
        box = layout.box()
        box.label(text="Space Switching Tools")
        
        # Try to use custom icon for Knot operator, with fallback
        row = box.row()
        if HAS_ICONS:
            try:
                knot_icon_id = get_icon_id("knot")
                if knot_icon_id != 0:
                    row.operator(AH_Knot.bl_idname, icon_value=knot_icon_id, text="Knot Constraint")
                else:
                    row.operator(AH_Knot.bl_idname, icon='CONSTRAINT', text="Knot Constraint")
            except:
                row.operator(AH_Knot.bl_idname, icon='CONSTRAINT', text="Knot Constraint")
        else:
            row.operator(AH_Knot.bl_idname, icon='CONSTRAINT', text="Knot Constraint")
        
        # Other buttons
        row = box.row()
        row.operator(AH_ShoulderLock.bl_idname, icon='COLORSET_03_VEC', text="Shoulder Lock")
        
        row = box.row()
        row.operator(AH_CopyTransforms.bl_idname, icon='COLORSET_04_VEC', text="Copy Transforms")
        
        # New Copy Rotation button
        row = box.row()
        row.operator(AH_CopyRotation.bl_idname, icon='COLORSET_06_VEC', text="Copy Rotation")
        
        layout.separator()
        
        # Keyframe cleanup section
        box = layout.box()
        box.label(text="Keyframe Cleanup")
        
        row = box.row()
        row.operator(AH_DecimateKeys.bl_idname, icon='COLORSET_02_VEC', text="Decimate Keyframes")
        
        row = box.row()
        row.prop(scene, "Factor", slider=True)
        
        layout.separator()
        
        # Animation baking section
        box = layout.box()
        box.label(text="Animation Baking")
        
        row = box.row()
        row.alert = True
        row.operator(AH_AnimationBake.bl_idname, icon='REC', text="Easy Bake Animation")
        
        row = box.row()
        row.operator(AH_DuplicateSelectedBonesAction.bl_idname, icon='COLORSET_09_VEC', text="Duplicate Selected Bones Action")
        
        sub_box = box.box()
        sub_box.label(text="Baking Options", icon='PREFERENCES')
        
        sub_box.prop(bakeprops, "smart_bake")
        
        if not bakeprops.smart_bake:
            row = sub_box.row(align=True)
            row.prop(bakeprops, "custom_frame_start", text="Start")
            row.prop(bakeprops, "custom_frame_end", text="End")
        
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