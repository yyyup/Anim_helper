import bpy

# Import panels with updated class names
from .panel1 import AH_AnimTools
from .panel2 import AH_MaterialTools
from .panel_action_management import AH_ActionManagement
from .panel_pose_library import AH_PoseLibraryPanel
from .panel_facial_auto import AH_FacialAutoProcessingPanel
from.panel_nla_transfer import AH_NLATransferPanel
from.panel_nla_smoothing import AH_NLASmoothingPanel
from .panel_audio_nla_consolidation import AH_AudioNLAConsolidationPanel

# Add panels to classes array
classes = (
    AH_MaterialTools,
    AH_AnimTools,
    AH_ActionManagement,
    AH_PoseLibraryPanel,
    AH_FacialAutoProcessingPanel,
    AH_NLATransferPanel,
    AH_NLASmoothingPanel,
    AH_AudioNLAConsolidationPanel,
)

def register_panels():
    """Register all panel classes"""
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister_panels():
    """Unregister all panel classes"""
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)