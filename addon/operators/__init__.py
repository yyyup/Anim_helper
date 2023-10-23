import bpy

from .animation_bake import AH_Animation_bake
from .decimate_ratio_75 import Anim_OP_Decimate
from .Delete_duplicate_mats import SIMPLE_AH_MaterialCleanUp
from .animation_bake import bakeprops
from .add_shoulder_lock import Anim_AH_Shoulder_lock
from .Add_copyT_and_reverse import Anim_H_Copy_T
from .Origin_XY import Anim_H_CenterObjectsXY
from .MakeCollection import Anim_H_MoveToNewCollection


classes = (bakeprops,
           Anim_AH_Shoulder_lock,
           AH_Animation_bake,
           Anim_OP_Decimate,
           SIMPLE_AH_MaterialCleanUp,
           Anim_H_Copy_T,
           Anim_H_CenterObjectsXY,
           Anim_H_MoveToNewCollection,
           
           )


def register_operators():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.Factor = bpy.props.FloatProperty(name= "Factor", default=0.75, min=0, max=1)  
    bpy.types.Scene.bprops = bpy.props.PointerProperty(type= bakeprops)
    
    

def unregister_operators():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    del bpy.types.Scene.Factor
    del bpy.types.Scene.bprops


