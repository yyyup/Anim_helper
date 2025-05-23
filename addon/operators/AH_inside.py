import bpy
from mathutils import Matrix

class AH_inside(bpy.types.Operator):
    bl_idname = "anim_h.inside"
    bl_label = "Parent With Preserved Animation"
    bl_description = "Parents selected EMPTYs to the active EMPTY while preserving animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            self.parent_multiple_with_preserved_animation(context)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}

    def parent_multiple_with_preserved_animation(self, context):
        selected = context.selected_objects
        parent = context.active_object

        if parent not in selected:
            raise Exception("The active object must be among the selected objects.")
        if parent.type != 'EMPTY':
            raise Exception("Active object (parent) must be an EMPTY.")
        if any(obj.type != 'EMPTY' for obj in selected):
            raise Exception("All selected objects must be EMPTYs.")

        children = [obj for obj in selected if obj != parent]
        if not children:
            raise Exception("Please select at least one EMPTY to parent to the active object.")

        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end

        for child in children:
            print(f"Processing {child.name}")

            temp_empty = bpy.data.objects.new(f"TEMP_{child.name}_Preserve", None)
            context.collection.objects.link(temp_empty)

            constraint = temp_empty.constraints.new('COPY_TRANSFORMS')
            constraint.target = child

            bpy.ops.object.select_all(action='DESELECT')
            temp_empty.select_set(True)
            context.view_layer.objects.active = temp_empty
            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=False,
                bake_types={'OBJECT'}
            )
            temp_empty.constraints.remove(constraint)

            world_matrix = child.matrix_world.copy()
            child.parent = parent
            child.matrix_parent_inverse = Matrix.Identity(4)
            child.matrix_world = world_matrix

            constraint = child.constraints.new('COPY_TRANSFORMS')
            constraint.target = temp_empty

            bpy.ops.object.select_all(action='DESELECT')
            child.select_set(True)
            context.view_layer.objects.active = child
            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                bake_types={'OBJECT'}
            )

            bpy.data.objects.remove(temp_empty, do_unlink=True)

        self.report({'INFO'}, f"Successfully parented {len(children)} empties to {parent.name} with preserved animations.")

