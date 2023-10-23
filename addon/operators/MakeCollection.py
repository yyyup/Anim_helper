import bpy
import logging

class Anim_H_MoveToNewCollection(bpy.types.Operator):
    bl_idname = "object.move_to_new_collection"
    bl_label = "Move to New Collection"
    bl_description = "Move each selected object and its children to a new collection named after the object"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = bpy.context.selected_objects.copy()

        for selected_object in selected_objects:
            # Create new collection and link it to the scene
            new_collection = bpy.data.collections.new(selected_object.name)
            bpy.context.scene.collection.children.link(new_collection)
            
            # Function to move object and its children to the new collection
            def move_to_collection(obj, collection):
                for child in obj.children:
                    move_to_collection(child, collection)
                
                for col in obj.users_collection:
                    col.objects.unlink(obj)
                collection.objects.link(obj)
            
            # Move selected object and its children to the new collection
            move_to_collection(selected_object, new_collection)
        
        # # Collapsing hierarchy in the outliner
        # for area in bpy.context.screen.areas:
        #     if area.type == 'OUTLINER':
        #         override = bpy.context.copy()
        #         override['area'] = area
        #         bpy.ops.outliner.show_one_level(override, open=False)
                
        self.report({'INFO'}, f"Moved {len(selected_objects)} objects to new collections and collapsed the hierarchy.")
        return {'FINISHED'}