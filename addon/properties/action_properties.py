import bpy
import bpy.props

class AH_ActionProperties(bpy.types.PropertyGroup):
    """Properties for action management"""
    keyword: bpy.props.StringProperty(
        name="Keyword",
        description="Keyword to search for in action names",
        default=""
    )