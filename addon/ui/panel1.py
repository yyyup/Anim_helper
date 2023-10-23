import bpy
import bpy.props

from ..operators.animation_bake import AH_Animation_bake
from ..operators.decimate_ratio_75 import Anim_OP_Decimate
from ..operators.Delete_duplicate_mats import SIMPLE_AH_MaterialCleanUp
from ..operators.add_shoulder_lock import Anim_AH_Shoulder_lock

class Panel1(bpy.types.Panel):
    bl_label = "Anim helper"
    bl_idname = "Anim_helper"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        
        scene = context.scene
        bprops = scene.bprops
        
        
        
        row = layout.row()
        col = layout.column()
        col.label(text= "Remove duplicate mats")
        col.operator(SIMPLE_AH_MaterialCleanUp.bl_idname, icon= 'SPHERE')
        col.separator()
        
        
        col.label(text= "add shoulder lock for fk chain")
        col.operator(Anim_AH_Shoulder_lock.bl_idname)
        col.separator()
        
        
        col.label(text= "decimate keyframes")
        col.operator(Anim_OP_Decimate.bl_idname)
        col.separator()
        
        col.prop(context.scene, "Factor")
        col.separator()
        col.operator(AH_Animation_bake.bl_idname)
        
        
        
        col.prop(bprops, "smart_bake")
        if not bprops.smart_bake:
            col.prop(bprops, "custom_frame_start", text="Start Frame")
            col.prop(bprops, "custom_frame_end", text="End Frame")
        
        col.prop(bprops, "visual_keying")
        col.prop(bprops, "only_selected_bones")
        col.prop(bprops, "clear_constraints")
        col.prop(bprops, "clear_parents")
        col.prop(bprops, "overwrite_current_action")
    
        
