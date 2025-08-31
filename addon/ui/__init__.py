import bpy

# Import panels with updated class names
from .panel1 import AH_AnimTools, AH_PT_SpaceSwitching, AH_PT_KeyframeCleanup, AH_PT_AnimationBaking, AH_PT_AnimToolsHelp
from .panel2 import AH_MaterialTools
from .panel_action_management import AH_ActionManagement
from .panel_facial_auto import AH_FacialAutoProcessingPanel
from.panel_nla_transfer import AH_NLATransferPanel
from.panel_nla_smoothing import AH_NLASmoothingPanel
from .panel_audio_nla_consolidation import AH_AudioNLAConsolidationPanel
from ..preferences import update_panel_categories
from .ah_nla_panel import AH_PT_NLA_AnimHelper
# Add panels to classes array
classes = (
    AH_MaterialTools,
    AH_AnimTools,
    AH_PT_SpaceSwitching,
    AH_PT_KeyframeCleanup,
    AH_PT_AnimationBaking,
    AH_PT_AnimToolsHelp,
    AH_ActionManagement,
    AH_FacialAutoProcessingPanel,
    AH_NLATransferPanel,
    AH_NLASmoothingPanel,
    AH_AudioNLAConsolidationPanel,
    AH_PT_NLA_AnimHelper,
)

def register_panels():
    """Register all panel classes"""
    from bpy.utils import register_class
    update_panel_categories()
    for cls in classes:
        register_class(cls)

def unregister_panels():
    """Unregister all panel classes"""
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)