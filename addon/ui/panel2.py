import bpy
import bpy.props

from ..operators.Delete_duplicate_mats import SIMPLE_AH_MaterialCleanUp
from ..operators.Origin_XY import Anim_H_CenterObjectsXY
from ..operators.MakeCollection import Anim_H_MoveToNewCollection
from ..operators.Facial_cleanup import AH_RenameAndCleanup, AH_Facialprops

from ..operators.Knot import ANIM_H_knot
from ..operators.add_shoulder_lock import Anim_AH_Shoulder_lock
from ..operators.Add_copyT_and_reverse import Anim_H_Copy_T
from ..operators.Delete_actions import AH_DeleteActions, AH_DeleteActionsProperties


class Panel2(bpy.types.Panel):
    bl_label = "Material Tools"
    bl_idname = "Material_Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        
        scene = context.scene
        
        
        
        
        row = layout.row()
        col = layout.column()
        col.label(text= "Extra Tools")
        col.operator(SIMPLE_AH_MaterialCleanUp.bl_idname, icon= 'SPHERE')
        col.operator(Anim_H_CenterObjectsXY.bl_idname)
        col.operator(Anim_H_MoveToNewCollection.bl_idname)
        
        
        col.label(text= "Space switching Tools")
        col.operator(ANIM_H_knot.bl_idname)
        col.operator(Anim_AH_Shoulder_lock.bl_idname)
        col.operator(Anim_H_Copy_T.bl_idname)
        col.separator()
        
        props = context.scene.Dprops
        layout.prop(props, "keyword")
        layout.operator(AH_DeleteActions.bl_idname, text="Delete Actions")
        layout.separator()
        
        
        
        
        
        
    
        
