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
from..operators.AH_inside import AH_inside
from ..operators.AH_world import AH_world  
from ..operators.AH_Swap import ANIM_H_OT_swap_parent_child
from ..operators.empty_size import AH_OT_EmptySizeGrow
from ..operators.empty_size import AH_OT_EmptySizeShrink
from ..operators.Offset import AH_offset
from ..operators.offset_cleanup import AH_offset_cleanup

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
        box = layout.box()
        #grid = box.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=True, align=True)
        
        # Reverse Hierarchy section (previously Space Switching Tools)
        
        box.label(text="Space Switching Tools")
        
        # Create a grid layout for the buttons in Reverse Hierarchy
        
        
        box.label(text="Locators", icon='EMPTY_ARROWS')
        col = box.column(align=True)
        
        
        # Knot Constraint button
        row = col.row()
        if HAS_ICONS and get_icon_id("knot") != 0:
            row.operator(AH_Knot.bl_idname, icon='EMPTY_ARROWS', text="T Constraint")
        else:
            row.operator(AH_Knot.bl_idname, icon='EMPTY_ARROWS', text="Knot Constraint")
            
        # Copy Transforms button  
        row = col.row(align=True)
        row.operator(AH_CopyTransforms.bl_idname, icon='EMPTY_AXIS', text="T Constraint B") 
        row.operator(AH_offset.bl_idname, icon='AUTOMERGE_OFF', text="offset")
        row.operator(AH_CopyRotation.bl_idname, icon='DRIVER_ROTATIONAL_DIFFERENCE', text="Copy Rotation")
        
        box.separator()
        
    
        box.label(text="Parent", icon='ORIENTATION_PARENT')
        row = box.row(align=True)
        row = box.row()
        row.operator(AH_inside.bl_idname, icon='ORIENTATION_PARENT', text="Inside")
        row.operator(AH_world.bl_idname, icon='WORLD', text="World")
        row.operator(ANIM_H_OT_swap_parent_child.bl_idname, icon='ARROW_LEFTRIGHT', text="swap")
        
        
        
        box.separator()
        
        
         # Bonus Tools section
        
        box.label(text="Bonus Tools", icon='TOOL_SETTINGS')
        row = box.row()
        row.operator(AH_offset_cleanup.bl_idname, icon='TRASH', text="cleanup")
        
        # Shoulder Lock button in Bonus Tools
        row = box.row()
        row.operator(AH_ShoulderLock.bl_idname, icon='CONSTRAINT_BONE', text="Shoulder Lock")
        
        box.separator()
        
        
        box.label(text="locator size")
        row = layout.row(align=True)       
        row.operator(AH_OT_EmptySizeGrow.bl_idname, icon='ADD', text="+")
        row.operator(AH_OT_EmptySizeShrink.bl_idname, icon='REMOVE', text="-")
        
        
        
        
       
        

        
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