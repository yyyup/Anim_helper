import bpy

# Import panels with updated class names
from .panel1 import AH_AnimTools
from .panel2 import AH_MaterialTools
from .panel_action_management import AH_ActionManagement

# Add panels to classes array
classes = (
    AH_MaterialTools,
    AH_AnimTools,
    AH_ActionManagement,
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