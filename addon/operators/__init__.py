import bpy

from .animation_bake import AH_Animation_bake
from .decimate_ratio_75 import Anim_OP_Decimate
from .Delete_duplicate_mats import SIMPLE_AH_MaterialCleanUp
from .animation_bake import bakeprops
from .add_shoulder_lock import Anim_AH_Shoulder_lock
from .Add_copyT_and_reverse import Anim_H_Copy_T
from .Origin_XY import Anim_H_CenterObjectsXY
from .MakeCollection import Anim_H_MoveToNewCollection
from .NLA_action import Anim_H_NLA
from .Knot import ANIM_H_knot
from .Delete_actions import AH_DeleteActions, AH_DeleteActionsProperties
from .Facial_cleanup import AH_RenameAndCleanup, AH_Facialprops
from .Snap_to_audio import Anim_H_SnapPlayhead_to_audio
from .Mirror_keys import AH_MIRROR_BONE_KEYFRAMES

classes = (bakeprops,
           Anim_AH_Shoulder_lock,
           AH_Animation_bake,
           Anim_OP_Decimate,
           SIMPLE_AH_MaterialCleanUp,
           Anim_H_Copy_T,
           Anim_H_CenterObjectsXY,
           Anim_H_MoveToNewCollection,
           Anim_H_NLA,
           ANIM_H_knot,
           AH_DeleteActions,
           AH_RenameAndCleanup,  
           AH_DeleteActionsProperties,
           AH_Facialprops,
           Anim_H_SnapPlayhead_to_audio,
           AH_MIRROR_BONE_KEYFRAMES
           
           
                    
           
           )


def register_operators():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    
    bpy.types.Scene.bprops = bpy.props.PointerProperty(type= bakeprops)
    bpy.types.Scene.Dprops = bpy.props.PointerProperty(type=AH_DeleteActionsProperties)
    bpy.types.Scene.fprops = bpy.props.PointerProperty(type=AH_Facialprops)
    
    
    
    

def unregister_operators():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    

    del bpy.types.Scene.fprops
    del bpy.types.Scene.Dprops  
    del bpy.types.Scene.bprops


