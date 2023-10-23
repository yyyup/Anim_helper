import bpy
from mathutils import Vector


def get_inactive_selected_object():
    for obj in bpy.context.selected_objects:
        if(obj.name_full != bpy.context.active_object.name_full):
            return obj
    


def create_offset_parent_constraint(child, parent, offset):
    # Add an empty object to serve as the offset target
    offset_target = bpy.data.objects.new(name="offset_target", object_data=None)
    bpy.context.scene.collection.objects.link(offset_target)
    offset_target.location = parent.location + offset
    offset_target.rotation_euler = parent.rotation_euler

    # Add a Copy Transforms constraint to the offset target, targeting the parent object
    constraint = offset_target.constraints.new('COPY_TRANSFORMS')
    constraint.target = parent

    # Add a Child Of constraint to the child object, targeting the offset target
    constraint = child.constraints.new('CHILD_OF')
    constraint.target = offset_target
    constraint.inverse_matrix = parent.matrix_world.inverted()

    for o in bpy.context.selected_objects:
        print(o.name + "is selected")

    # Return the offset target for later use
    return offset_target

# Example usage:

child_object = get_inactive_selected_object()

if(child_object is None):
    print("Please select at least 2 objects")
else:
    parent_object = bpy.context.active_object
    offset_vector = Vector((0.0, 0.0, 0.0))
    offset_target = create_offset_parent_constraint(child_object, parent_object, offset_vector)