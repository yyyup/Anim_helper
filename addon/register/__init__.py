import bpy

def register_addon():
    """Register all components of the addon"""
    # Register properties first
    from ..properties import register_properties
    register_properties()
    
    # Register operators
    from ..operators import register_operators
    register_operators()

    # Register UI panels
    from ..ui import register_panels
    register_panels()
   
def unregister_addon():
    """Unregister all components of the addon in reverse order"""
    # Unregister UI panels first
    from ..ui import unregister_panels
    unregister_panels()

    # Unregister operators
    from ..operators import unregister_operators
    unregister_operators()
    
    # Unregister properties last
    from ..properties import unregister_properties
    unregister_properties()