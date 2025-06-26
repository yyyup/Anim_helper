import bpy

ROOT_MODULE = __package__.split('.')[0]


class AH_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = ROOT_MODULE

    tab_name: bpy.props.StringProperty(
        name="Tab Name",
        description="Name of the sidebar tab where panels appear",
        default="AH Helper",
        update=lambda self, context: refresh_panel_categories()
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "tab_name")


def update_panel_categories():
    """Update the bl_category for all registered panels"""
    import importlib
    ui_module = importlib.import_module(f"{ROOT_MODULE}.addon.ui")
    prefs = bpy.context.preferences.addons[ROOT_MODULE].preferences
    for cls in ui_module.classes:
        cls.bl_category = prefs.tab_name


def refresh_panel_categories():
    """Reload UI panels so category changes take effect immediately"""
    import importlib
    from bpy.utils import unregister_class, register_class
    ui_module = importlib.import_module(f"{ROOT_MODULE}.addon.ui")
    prefs = bpy.context.preferences.addons[ROOT_MODULE].preferences
    for cls in ui_module.classes:
        try:
            unregister_class(cls)
        except Exception:
            pass
        cls.bl_category = prefs.tab_name
        register_class(cls)


def register_preferences():
    bpy.utils.register_class(AH_AddonPreferences)
    update_panel_categories()

def unregister_preferences():
    bpy.utils.unregister_class(AH_AddonPreferences)

