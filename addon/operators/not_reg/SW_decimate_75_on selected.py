import bpy

def decimate_fcurve(fcurve, factor):
    points = fcurve.keyframe_points
    n_points = len(points)

    if n_points <= 2:
        return

    indices_to_remove = sorted(range(1, n_points - 1), key=lambda i: points[i].co.y, reverse=True)[:int((n_points - 2) * factor)]

    for index in sorted(indices_to_remove, reverse=True):
        points.remove(points[index])

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

        # Iterate through the F-Curves in the action
        for fcurve in action.fcurves:
            # Check if the F-Curve belongs to the selected bone
            if bone.name in fcurve.data_path:
                # Decimate the F-Curve with a 75% ratio
                decimate_fcurve(fcurve, 0.75)