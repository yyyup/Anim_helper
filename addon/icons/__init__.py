import os
import bpy
import bpy.utils.previews

# Collection of icon previews
icons_collection = None

def get_icon_id(icon_name):
    """Get icon ID by name"""
    global icons_collection
    if icons_collection is not None:
        return icons_collection[icon_name].icon_id
    return 0

def register_icons():
    """Register custom icons"""
    global icons_collection
    icons_collection = bpy.utils.previews.new()
    
    # Get the directory of this file
    icons_dir = os.path.dirname(__file__)
    
    # Load all icons from the icons directory
    icon_files = [f for f in os.listdir(icons_dir) if f.endswith(".png")]
    
    for icon_file in icon_files:
        icon_name = os.path.splitext(icon_file)[0]
        icons_collection.load(icon_name, os.path.join(icons_dir, icon_file), 'IMAGE')
        print(f"Loaded icon: {icon_name}")

def unregister_icons():
    """Unregister custom icons"""
    global icons_collection
    if icons_collection is not None:
        bpy.utils.previews.remove(icons_collection)
        icons_collection = None