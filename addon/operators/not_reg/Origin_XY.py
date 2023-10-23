import bpy

# Get all selected objects
selected_objects = bpy.context.selected_objects

for obj in selected_objects:
    # Calculate the difference between object's location and world origin for X and Y
    delta_x = 0 - obj.location.x
    delta_y = 0 - obj.location.y
    
    # Apply the delta to center the object on X and Y
    obj.location.x += delta_x
    obj.location.y += delta_y
