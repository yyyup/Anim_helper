import bpy

class Anim_AH_Shoulder_lock(bpy.types.Operator):
     #add shoulder lock#

    bl_idname = "shoulder.lock"
    bl_label = "add Shoulder lock"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("HERE")

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
            constraint = empty.constraints.new(type="COPY_ROTATION")
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
            constraint = bone.constraints.new(type="COPY_ROTATION")
            constraint.target = empty
            

        # Switch to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Select the last created empty
        created_empties[-1].select_set(True)

        # Set the active object to the last created empty
        bpy.context.view_layer.objects.active = created_empties[-1]

        # get the active object
        obj = bpy.context.active_object

        # get all the F-curves in the object's animation data
        fcurves = obj.animation_data.action.fcurves

        # add the CYCLES modifier to each F-curve for the XYZ location
        for fcurve in fcurves:
            if fcurve.data_path == "rotation_euler":
                fcurve.modifiers.new('CYCLES')
                
        # move each F-curve for the object's rotation by 2 frames
        for empty in created_empties:
            empty_animation_data = empty.animation_data
            if empty_animation_data is not None:
                empty_action = empty_animation_data.action
                if empty_action is not None:
                    for fcurve in empty_action.fcurves:
                        if fcurve.data_path == "rotation_euler":
                            for keyframe in fcurve.keyframe_points:
                                keyframe.co.x += 2
                            fcurve.update()
                            
        return {'FINISHED'}