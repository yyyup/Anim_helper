import bpy
import bpy.props

class AH_PoseLibraryProperties(bpy.types.PropertyGroup):
    """Properties for pose library integration"""
    pose_name: bpy.props.StringProperty(
        name="Pose Name",
        description="Name of the pose to apply",
        default=""
    )
