import bpy

# Import all operator classes with standardized naming
from .animation_bake import AH_AnimationBake
from .decimate_ratio_75 import AH_DecimateKeys
from .Delete_duplicate_mats import AH_MaterialCleanup
from .add_shoulder_lock import AH_ShoulderLock
from .Add_copyT_and_reverse import AH_CopyTransforms
from .Copy_rotation import AH_CopyRotation
from .Knot_offset import AH_KnotOffset
from .Origin_XY import AH_CenterObjectsXY
from .MakeCollection import AH_MoveToNewCollection
from .NLA_action import AH_DuplicateSelectedBonesAction
from .Knot import AH_Knot
from .Delete_actions import AH_DeleteActions
from .Facial_cleanup import AH_RenameAndCleanup
from .Snap_to_audio import AH_SnapPlayheadToStrip
from .Mirror_keys import AH_MirrorBoneKeyframes

# Define all classes that should be registered
classes = (
    AH_AnimationBake,
    AH_ShoulderLock,
    AH_DecimateKeys,
    AH_MaterialCleanup,
    AH_CopyTransforms,
    AH_CopyRotation,
    AH_KnotOffset,
    AH_CenterObjectsXY,
    AH_MoveToNewCollection,
    AH_DuplicateSelectedBonesAction,
    AH_Knot,
    AH_DeleteActions,
    AH_RenameAndCleanup,
    AH_SnapPlayheadToStrip,
    AH_MirrorBoneKeyframes,
)

def register_operators():
    """Register all operator classes"""
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister_operators():
    """Unregister all operator classes"""
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)