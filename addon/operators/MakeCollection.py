import bpy

class AH_MoveToNewCollection(bpy.types.Operator):
    """Organize objects by moving each selected object and its children to a new collection"""
    bl_idname = "object.move_to_new_collection"
    bl_label = "Move to New Collection"
    bl_description = "Move each selected object and its children to a new collection named after the object"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get a copy of the currently selected objects
        selected_objects = context.selected_objects.copy()
        
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}
        
        collections_created = 0
        
        for selected_object in selected_objects:
            try:
                # Create new collection and link it to the scene
                new_collection = bpy.data.collections.new(selected_object.name)
                context.scene.collection.children.link(new_collection)
                
                # Move object and its children to the new collection
                self._move_to_collection(selected_object, new_collection)
                collections_created += 1
                
            except Exception as e:
                self.report({'WARNING'}, f"Could not process {selected_object.name}: {str(e)}")
                continue
                
        if collections_created > 0:
            self.report({'INFO'}, f"Moved {collections_created} objects to new collections.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No collections created.")
            return {'CANCELLED'}
    
    def _move_to_collection(self, obj, collection):
        """Recursively move an object and its children to a collection"""
        # First process all children recursively
        for child in obj.children:
            self._move_to_collection(child, collection)
        
        # Then unlink the object from all current collections and link to the new one
        for col in obj.users_collection:
            col.objects.unlink(obj)
        
        collection.objects.link(obj)