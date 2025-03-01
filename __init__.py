import bpy


bl_info = {
    "name": "Anim Helper",
    "description": "Animation helper tools for Blender",
    "author": "CGStuff",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > AH Helper",
    "category": "Animation",
}

def register():
    from .addon.register import register_addon
    register_addon()
    
def unregister():
    from .addon.register import unregister_addon
    unregister_addon()