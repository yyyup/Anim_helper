# addon/properties/ah_nla_props.py
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty, StringProperty

class AH_NLAProperties(PropertyGroup):
    duplicate_actions: BoolProperty(default=True, name="Duplicate Actions")
    frame_offset: IntProperty(default=0, name="Frame Offset")
    name_suffix: StringProperty(default=".dupe", name="Name Suffix")
