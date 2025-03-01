import bpy
import bpy.props

# Import operators with standardized naming
from ..operators.Delete_duplicate_mats import AH_MaterialCleanup
from ..operators.Origin_XY import AH_CenterObjectsXY
from ..operators.MakeCollection import AH_MoveToNewCollection
from ..operators.Delete_actions import AH_DeleteActions

class AH_MaterialTools(bpy.types.Panel):
    """Material tools panel in the 3D View sidebar"""
    bl_label = "Material Tools"
    bl_idname = "AH_PT_MaterialTools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AH Helper'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Object tools section
        box = layout.box()
        box.label(text="Object Tools")
        
        # Blue themed button for material cleanup
        row = box.row()
        row.operator(AH_MaterialCleanup.bl_idname, icon='COLORSET_01_VEC', text="Clean Materials")
        
        # Green themed button for centering objects
        row = box.row()
        row.operator(AH_CenterObjectsXY.bl_idname, icon='COLORSET_03_VEC', text="Center Objects in XY")
        
        # Purple themed button for collection management
        row = box.row()
        row.operator(AH_MoveToNewCollection.bl_idname, icon='COLORSET_04_VEC', text="Move to New Collection")
        
        # Action management section - moved from redundant space switching section
        box = layout.box()
        box.label(text="Quick Action Management")
        
        props = context.scene.Dprops
        box.prop(props, "keyword")
        
        # Orange themed button for action deletion
        row = box.row()
        row.alert = True  # Makes the button reddish for destructive actions
        row.operator(AH_DeleteActions.bl_idname, text="Delete Actions", icon='TRASH')
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='MATERIAL')