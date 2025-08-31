import bpy
from bpy.utils import register_class, unregister_class
from .bake_properties import AH_BakeProperties
from .facial_properties import AH_FacialProperties
from .action_properties import AH_ActionProperties
from .ah_nla_props import AH_NLAProperties   # <-- fixed spacing
from bpy.props import PointerProperty

property_classes = (
    AH_BakeProperties,
    AH_FacialProperties,
    AH_ActionProperties,
    AH_NLAProperties,
)

# host → [(attr_name, PropertyGroup)]
_POINTERS = {
    bpy.types.Scene: [
        ("bprops", AH_BakeProperties),
        ("fprops", AH_FacialProperties),
        ("Dprops", AH_ActionProperties),
        ("Factor", AH_ActionProperties),   # if you really want both names
        ("ah_nla", AH_NLAProperties),      
    ]
}

def _safe_register_class(cls):
    try:
        register_class(cls)
    except ValueError:
        try: unregister_class(cls)
        except Exception: pass
        register_class(cls)

def _safe_unregister_class(cls):
    try:
        unregister_class(cls)
    except Exception:
        pass

def register_properties():
    # 1) classes first
    for cls in property_classes:
        _safe_register_class(cls)
    # 2) pointers after classes
    for host, pairs in _POINTERS.items():
        for attr, pg in pairs:
            if not hasattr(host, attr):
                setattr(host, attr, PointerProperty(type=pg))

def unregister_properties():
    # 1) remove pointers first
    for host, pairs in _POINTERS.items():
        for attr, _ in reversed(pairs):
            if hasattr(host, attr):
                delattr(host, attr)
    # 2) classes after pointers
    for cls in reversed(property_classes):
        _safe_unregister_class(cls)
