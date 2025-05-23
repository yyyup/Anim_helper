import bpy
from mathutils import Matrix

class AH_world(bpy.types.Operator):
    bl_idname = "anim_h.world"
    bl_label = "Unparent With Preserved Animation"
    bl_description = "Unparents selected EMPTYs while preserving their world animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            self.unparent_with_preserved_animation(context)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

    def unparent_with_preserved_animation(self, context):
        selected = context.selected_objects
        empties = [obj for obj in selected if obj.type == 'EMPTY' and obj.parent is not None]

        if not empties:
            raise Exception("Select one or more parented EMPTY objects.")

        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end

        for obj in empties:
            print(f"Processing {obj.name}")

            # Create temporary helper empty
            temp_empty = bpy.data.objects.new(f"TEMP_{obj.name}_Preserve", None)
            context.collection.objects.link(temp_empty)

            # Copy transforms from original object
            constraint = temp_empty.constraints.new('COPY_TRANSFORMS')
            constraint.target = obj

            # Bake temp empty to preserve world animation
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

            # Unparent while keeping transform
            matrix_world = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = matrix_world

            # Apply animation from temp back to original object
            constraint = obj.constraints.new('COPY_TRANSFORMS')
            constraint.target = temp_empty

            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                bake_types={'OBJECT'}
            )

            # Cleanup temp
            bpy.data.objects.remove(temp_empty, do_unlink=True)

        self.report({'INFO'}, f"Successfully unparented {len(empties)} empties while preserving animation.")
