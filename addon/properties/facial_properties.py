import bpy
import bpy.props

class AH_FacialProperties(bpy.types.PropertyGroup):
    """Properties for facial animation cleanup"""
    rig_action_name: bpy.props.StringProperty(
        name="Rig Action Name",
        description="Name for the renamed rig action",
        default="XXX_RA_Speech_01"
    )
    shapekey_action_name: bpy.props.StringProperty(
        name="Shapekey Action Name",
        description="Name for the renamed shapekey action",
        default="XXX_SA_Speech_01"
    )
    body_mesh_name: bpy.props.StringProperty(
        name="Body Mesh Name",
        description="Name of the body mesh with shapekeys",
        default=""
    )