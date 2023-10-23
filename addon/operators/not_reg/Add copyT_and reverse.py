import bpy

class Anim_OP_Copy_T(bpy.types.Operator):
     #add lights to the scene#

    bl_idname = "Anim_OP_Copy_T"
    bl_label = "add copyT_reverse"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("HERE")
        return {'FINISHED'}

# Get the selected bones in pose mode
selected_bones = bpy.context.selected_pose_bones

# Create an empty list to store the created empties
created_empties = []

# Loop through each selected bone
for bone in selected_bones:
    # Create an empty at the location of the bone
    empty = bpy.data.objects.new("Empty", None)
    empty.location = bone.matrix.to_translation()
    
    # Link the empty object to the current scene collection
    bpy.context.collection.objects.link(empty)

    # Get the armature that contains the selected bone
    armature = bone.id_data

    # Add a copy transform constraint to the empty
    constraint = empty.constraints.new(type="COPY_TRANSFORMS")
    constraint.target = armature
    constraint.subtarget = bone.name

    # Add the created empty to the list
    created_empties.append(empty)

# Store the active object
original_active_object = bpy.context.active_object

# Set the active object to the armature and switch to object mode
bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode='OBJECT')

# Deselect all objects
bpy.ops.object.select_all(action='DESELECT')

# Select the created empties and set the first one as the active object
for empty in created_empties:
    empty.select_set(True)
bpy.context.view_layer.objects.active = created_empties[0]

# Bake the action with the specified options
bpy.ops.nla.bake(
    frame_start=bpy.context.scene.frame_start,
    frame_end=bpy.context.scene.frame_end,
    only_selected=True,
    visual_keying=True,
    clear_constraints=True,
    use_current_action=True,
    bake_types={"OBJECT"}
)

# Set the original active object back and switch back to pose mode
bpy.context.view_layer.objects.active = original_active_object
bpy.ops.object.mode_set(mode='POSE')

# Add the Copy Transforms constraint to the original selected bones
for i, bone in enumerate(selected_bones):
    # Get the corresponding baked empty
    empty = created_empties[i]

    # Add a Copy Transforms constraint to the bone
    constraint = bone.constraints.new(type="COPY_TRANSFORMS")
    constraint.target = empty