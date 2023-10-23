import bpy

class SIMPLE_AH_DeleteObjects(bpy.types.Operator):
    bl_idname = "simple.delete_objects"
    bl_label = "Delete Objects"
    bl_options = {'REGISTER', 'UNDO'}

# Define a function that iterates over all collections in the scene and deletes objects that contain ".0" in the name, but not if they have a fake user enabled on their data
def execute(self, context):
    for collection in bpy.data.collections:
        for obj in collection.objects:
            if ".0" in obj.name and not obj.data.use_fake_user:
                bpy.data.objects.remove(obj)

    return {'FINISHED'}

                    