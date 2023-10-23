import bpy

# get the panels you want
from .panel1 import Panel1


# add them to classes array
classes = (
    Panel1,
)

# this function goes through the classes array and registeres them
def register_panels():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister_panels():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)