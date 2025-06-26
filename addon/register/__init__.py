import bpy

def register_addon():
    """Register all components of the addon"""
    # Register icons first
    from ..icons import register_icons
    register_icons()
    
    # Register properties
    from ..properties import register_properties
    register_properties()
    
    # Register operators
    from ..operators import register_operators
    register_operators()

    # Register addon preferences
    from ..preferences import register_preferences
    register_preferences()

    # Register UI panels
    from ..ui import register_panels
    register_panels()
   
def unregister_addon():
    """Unregister all components of the addon in reverse order"""
    # Unregister UI panels first
    from ..ui import unregister_panels
    unregister_panels()

    # Unregister addon preferences
    from ..preferences import unregister_preferences
    unregister_preferences()

    # Unregister operators
    from ..operators import unregister_operators
    unregister_operators()
    
    # Unregister properties
    from ..properties import unregister_properties
    unregister_properties()
    
    # Unregister icons last
    from ..icons import unregister_icons
    unregister_icons()

