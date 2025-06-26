from importlib import import_module


# (module_path, register_func, unregister_func)
COMPONENTS = [
    ("..icons", "register_icons", "unregister_icons"),
    ("..properties", "register_properties", "unregister_properties"),
    ("..operators", "register_operators", "unregister_operators"),
    ("..ui", "register_panels", "unregister_panels"),
]


def register_addon():
    """Register all components of the addon."""
    for module_name, register_func, _ in COMPONENTS:
        module = import_module(module_name, __package__)
        getattr(module, register_func)()


def unregister_addon():
    """Unregister all components of the addon in reverse order."""
    for module_name, _, unregister_func in reversed(COMPONENTS):
        module = import_module(module_name, __package__)
        getattr(module, unregister_func)()