import bpy

# get the panels you want
from .panel1 import Panel1
from .panel2 import Panel2


# add them to classes array
classes = (
    Panel2,
    Panel1,
)

# this function goes through the classes array and registeres them
def register_panels():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    bpy.types.Scene.rig_action_name = bpy.props.StringProperty(
        name="Rig Action Name",
        default="Renamed_Rig_Action"
    )
    bpy.types.Scene.shapekey_action_name = bpy.props.StringProperty(
        name="Shapekey Action Name",
        default="Renamed_Shapekey_Action"
    )
    bpy.types.Scene.body_mesh_name = bpy.props.StringProperty(
        name="Body Mesh Name",
        default=""
    )



def unregister_panels():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    del bpy.types.Scene.rig_action_name
    del bpy.types.Scene.shapekey_action_name
    del bpy.types.Scene.body_mesh_name