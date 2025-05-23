import bpy
import bpy.props

# Import operators
from ..operators.Delete_actions import AH_DeleteActions
from ..operators.Snap_to_audio import AH_SnapPlayheadToStrip
from ..operators.Mirror_keys import AH_MirrorBoneKeyframes
from ..operators.Facial_cleanup import AH_RenameAndCleanup


class AH_ActionManagement(bpy.types.Panel):
    """Action Management panel in the 3D View sidebar"""
    bl_label = "Action Management"
    bl_idname = "AH_PT_ActionManagement"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        deleteprops = scene.Dprops
        
        # Action management section
        box = layout.box()
        box.label(text="Action Management")
        box.prop(deleteprops, "keyword")
        box.operator(AH_DeleteActions.bl_idname, text="Delete Actions", icon='TRASH')
        box.operator(AH_SnapPlayheadToStrip.bl_idname, text="Snap to Audio", icon='SOUND')
        box.operator(AH_MirrorBoneKeyframes.bl_idname, text="Mirror Selected Keys", icon='MOD_MIRROR')
        
        # Facial animation section
        box = layout.box()
        box.label(text="Facial Animation")
        fprops = scene.fprops
        box.prop(fprops, 'rig_action_name')
        box.prop(fprops, 'shapekey_action_name')
        box.prop_search(fprops, 'body_mesh_name', scene, 'objects', text="Body Mesh")
        box.operator(AH_RenameAndCleanup.bl_idname, text="Rename and Cleanup", icon='CHECKMARK')
        