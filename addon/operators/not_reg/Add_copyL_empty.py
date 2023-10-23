import bpy


class Anim_OP_Copy_L(bpy.types.Operator):
     #add lights to the scene#

    bl_idname = "Anim_OP_Copy_L"
    bl_label = "add copyL_empty"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("HERE")
        return {'FINISHED'}


# Get the selected bones in pose mode
selected_bones = bpy.context.selected_pose_bones

# Loop through each selected bone
for bone in selected_bones:
    # Create an empty at the location of the bone
    empty = bpy.data.objects.new("Empty", None) 
    empty.location = bone.matrix.to_translation()
    
    # Link the empty to the current collection
    bpy.context.scene.collection.objects.link(empty)

    # Get the armature that contains the selected bone
    armature = bone.id_data

    # Add a copy location constraint to the empty
    constraint = empty.constraints.new(type="COPY_LOCATION")
    constraint.target = armature
    constraint.subtarget = bone.name
