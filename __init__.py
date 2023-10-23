import bpy


bl_info = {
    "name": "Anim Helper",
    "description": "anim helper tools",
    "author": "HAssan",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "category": "3d View",}

def register():
    from .addon.register import register_addon
    register_addon()
    
  
def unregister():
    from .addon.register import unregister_addon
    unregister_addon()
    