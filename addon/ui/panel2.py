import bpy
import bpy.props

from ..operators.Delete_duplicate_mats import SIMPLE_AH_MaterialCleanUp
from ..operators.Origin_XY import Anim_H_CenterObjectsXY
from ..operators.MakeCollection import Anim_H_MoveToNewCollection


class Panel2(bpy.types.Panel):
    bl_label = "Material Tools"
    bl_idname = "Material_Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        
        scene = context.scene
        bprops = scene.bprops
        
        
        
        row = layout.row()
        col = layout.column()
        col.label(text= "Extra Tools")
        col.operator(SIMPLE_AH_MaterialCleanUp.bl_idname, icon= 'SPHERE')
        col.operator(Anim_H_CenterObjectsXY.bl_idname)
        col.operator(Anim_H_MoveToNewCollection.bl_idname)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
        
