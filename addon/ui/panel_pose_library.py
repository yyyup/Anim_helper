import bpy

from ..operators.pose_library import AH_ApplyPose
from ..properties.pose_library_properties import AH_PoseLibraryProperties

class AH_PoseLibraryPanel(bpy.types.Panel):
    """Pose Library tools"""
    bl_label = "Pose Library"
    bl_idname = "AH_PT_PoseLibrary"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'

    def draw(self, context):
        layout = self.layout
        props = context.scene.poseprops
        obj = context.object

        if obj and obj.type == 'ARMATURE' and obj.pose_library:
            layout.prop_search(props, "pose_name", obj.pose_library, "pose_markers", text="Pose")
            op = layout.operator(AH_ApplyPose.bl_idname, text="Apply Pose", icon='POSE_HLT')
            op.pose_name = props.pose_name
        else:
            layout.label(text="Select an armature with a pose library", icon='ERROR')

    def draw_header(self, context):
        self.layout.label(icon='POSE_HLT')
