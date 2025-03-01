import bpy
import bpy.props

class AH_BakeProperties(bpy.types.PropertyGroup):
    """Properties for animation baking"""
    smart_bake: bpy.props.BoolProperty(
        name="Smart Bake", 
        default=True, 
        description="Automatically detect keyframe range for baking"
    )
    custom_frame_start: bpy.props.IntProperty(
        name="Custom Start Frame", 
        default=1, 
        description="Specify start frame for baking"
    )
    custom_frame_end: bpy.props.IntProperty(
        name="Custom End Frame", 
        default=250, 
        description="Specify end frame for baking"
    )
    only_selected_bones: bpy.props.BoolProperty(
        name="Only Selected Bones", 
        default=True,
        description="Only bake selected bones"
    )
    visual_keying: bpy.props.BoolProperty(
        name="Visual Keying", 
        default=True,
        description="Use visual keying for baking"
    )
    clear_constraints: bpy.props.BoolProperty(
        name="Clear Constraints", 
        default=True,
        description="Remove constraints after baking"
    )
    clear_parents: bpy.props.BoolProperty(
        name="Clear Parents", 
        default=True,
        description="Clear parent relationship after baking"
    )
    overwrite_current_action: bpy.props.BoolProperty(
        name="Overwrite Current Action", 
        default=True,
        description="Use existing action instead of creating a new one"
    )