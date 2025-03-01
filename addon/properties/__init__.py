import bpy

from .bake_properties import AH_BakeProperties
from .facial_properties import AH_FacialProperties
from .action_properties import AH_ActionProperties

# List of all property groups to register
property_classes = (
    AH_BakeProperties,
    AH_FacialProperties,
    AH_ActionProperties,
)

def register_properties():
    """Register all property groups"""
    from bpy.utils import register_class
    
    for cls in property_classes:
        register_class(cls)
    
    # Register property pointers
    bpy.types.Scene.bprops = bpy.props.PointerProperty(type=AH_BakeProperties)
    bpy.types.Scene.fprops = bpy.props.PointerProperty(type=AH_FacialProperties)
    bpy.types.Scene.Dprops = bpy.props.PointerProperty(type=AH_ActionProperties)
    
    # Add Factor property for decimation
    bpy.types.Scene.Factor = bpy.props.FloatProperty(
        name="Decimate Factor", 
        default=0.75, 
        min=0.1, 
        max=1.0,
        description="Amount of keyframes to keep (0.75 = keep 75%)"
    )

def unregister_properties():
    """Unregister all property groups in reverse order"""
    # Unregister property pointers
    del bpy.types.Scene.Factor
    del bpy.types.Scene.Dprops
    del bpy.types.Scene.fprops
    del bpy.types.Scene.bprops
    
    # Unregister classes
    from bpy.utils import unregister_class
    
    for cls in reversed(property_classes):
        unregister_class(cls)