import bpy

# Get the selected bones in pose mode
selected_bones = bpy.context.selected_pose_bones

# Loop through the selected bones
for bone in selected_bones:
    # Get the armature that contains the selected bone
    armature = bone.id_data

    # Check if the armature has animation data and an action
    if armature.animation_data and armature.animation_data.action:
        # Get the action associated with the armature
        action = armature.animation_data.action

        # Create a list to store F-Curves to be removed
        fcurves_to_remove = []

        # Iterate through the F-Curves in the action
        for fcurve in action.fcurves:
            # Check if the F-Curve belongs to the selected bone and is a rotation or scale F-Curve
            if bone.name in fcurve.data_path and ("location" in fcurve.data_path or "scale" in fcurve.data_path):
                # Add the F-Curve to the list of F-Curves to be removed
                fcurves_to_remove.append(fcurve)

        # Remove the F-Curves in the list
        for fcurve in fcurves_to_remove:
            action.fcurves.remove(fcurve)