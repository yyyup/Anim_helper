import bpy
import bpy.props

from ..operators.animation_bake import AH_Animation_bake
from ..operators.decimate_ratio_75 import Anim_OP_Decimate
from ..operators.add_shoulder_lock import Anim_AH_Shoulder_lock
from ..operators.Add_copyT_and_reverse import Anim_H_Copy_T
from ..operators.NLA_action import Anim_H_NLA
from ..operators.Knot import ANIM_H_knot
from ..operators.Delete_actions import AH_DeleteActions, AH_DeleteActionsProperties
from ..operators.Facial_cleanup import AH_RenameAndCleanup, AH_Facialprops
from ..operators.Snap_to_audio import Anim_H_SnapPlayhead_to_audio
from ..operators.Mirror_keys import AH_MIRROR_BONE_KEYFRAMES

class Panel1(bpy.types.Panel):
    bl_label = "Anim Tools"
    bl_idname = "Anim_Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        
        scene = context.scene
        bakeprops = scene.bprops
        Deleteprops = context.scene.Dprops
        
        
        
        row = layout.row()
        col = layout.column()
        
        
        
        col.label(text= "Space switching Tools")
        col.operator(ANIM_H_knot.bl_idname)
        col.operator("shoulder.lock")
        col.operator("anim_h.copy_t")
        col.separator()
        
        layout.separator()
        
        layout.prop(Deleteprops, "keyword")
        layout.operator(AH_DeleteActions.bl_idname, text="Delete Actions")
        layout.separator()
        layout.operator(Anim_H_SnapPlayhead_to_audio.bl_idname, text="Snap to audio")
        layout.operator(AH_MIRROR_BONE_KEYFRAMES.bl_idname, text="Mirror selected keys")
        
        
        layout = self.layout
        
        
        
        fprops = context.scene.fprops
        
        layout.label(text="Rename Actions:")
        layout.prop(fprops, 'rig_action_name')
        layout.prop(fprops, 'shapekey_action_name')
        layout.prop_search(fprops, 'body_mesh_name', context.scene, 'objects', text="Body Mesh")
        layout.separator()
        layout.operator(AH_RenameAndCleanup.bl_idname, text="Rename and Cleanup")
        
        
        
        col.label(text= "Keyframe CleanUp")
        col.operator(Anim_OP_Decimate.bl_idname)
        
        
        col.prop(context.scene, "Factor")
        
        
        col.operator(AH_Animation_bake.bl_idname)
        
        col.operator(Anim_H_NLA.bl_idname)
        
        
        
        
        
        col.prop(bakeprops, "smart_bake")
        if not bakeprops.smart_bake:
            col.prop(bakeprops, "custom_frame_start", text="Start Frame")
            col.prop(bakeprops, "custom_frame_end", text="End Frame")
        
        col.prop(bakeprops, "visual_keying")
        col.prop(bakeprops, "only_selected_bones")
        col.prop(bakeprops, "clear_constraints")
        col.prop(bakeprops, "clear_parents")
        col.prop(bakeprops, "overwrite_current_action")
    
        
