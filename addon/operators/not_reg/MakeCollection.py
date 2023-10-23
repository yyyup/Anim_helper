import bpy
import logging

log = logging.getLogger()

selected_objects = bpy.context.selected_objects

for selected_object in selected_objects:
    name = selected_object.name
    log.info("Name of selected " + name)
    collections = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collections)
    
    #objects = bpy.ops.object.select_pattern(pattern=f"*{name}*")
#    objs = bpy.context.selected_objects
    coll = collections # bpy.data.collections[name]
    
    cols = selected_object.users_collection
    coll.objects.link(selected_object)
    log.info(coll.objects)
    for col in cols:
        col.objects.unlink(selected_object)
            
    for child in selected_object.children:
        log.info(child)
        log.info(type(child))
        coll.objects.link(child)
        bpy.context.scene.collection.objects.unlink(child)