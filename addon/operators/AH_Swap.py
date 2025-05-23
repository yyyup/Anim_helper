import bpy
from mathutils import Matrix

class ANIM_H_OT_swap_parent_child(bpy.types.Operator):
    bl_idname = "anim_h.swap_parent_child"
    bl_label = "Swap Parent-Child with Preserved Hierarchy"
    bl_description = "Swap parent-child relationship between two selected objects while preserving animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            self.swap_parent_child_preserve_hierarchy(context)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}

    def swap_parent_child_preserve_hierarchy(self, context):
        selected = context.selected_objects
        new_parent = context.active_object

        if len(selected) != 2:
            raise Exception("Please select exactly 2 objects to swap parent-child relationship.")

        new_child = [obj for obj in selected if obj != new_parent][0]

        if new_child == new_parent:
            raise Exception("Cannot parent an object to itself.")

        print(f"Swapping: {new_parent.name} ⇄ {new_child.name}")

        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end

        original_parent = new_child.parent

        if new_parent == original_parent:
            raise Exception("Selected new parent is already the parent of the new child.")

        temp_parent = bpy.data.objects.new(f"TEMP_{new_parent.name}", None)
        temp_child = bpy.data.objects.new(f"TEMP_{new_child.name}", None)
        context.collection.objects.link(temp_parent)
        context.collection.objects.link(temp_child)

        temp_parent.matrix_world = new_parent.matrix_world.copy()
        temp_child.matrix_world = new_child.matrix_world.copy()

        con_p = temp_parent.constraints.new('COPY_TRANSFORMS')
        con_p.target = new_parent

        con_c = temp_child.constraints.new('COPY_TRANSFORMS')
        con_c.target = new_child

        bpy.ops.object.select_all(action='DESELECT')
        temp_parent.select_set(True)
        temp_child.select_set(True)
        context.view_layer.objects.active = temp_parent
        bpy.ops.nla.bake(
            frame_start=frame_start,
            frame_end=frame_end,
            only_selected=True,
            visual_keying=True,
            clear_constraints=False,
            bake_types={'OBJECT'}
        )

        temp_parent.constraints.remove(con_p)
        temp_child.constraints.remove(con_c)

        for obj in (new_parent, new_child):
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        if new_child == new_parent:
            raise Exception("Cannot make an object its own parent.")

        new_child.parent = new_parent
        new_child.matrix_parent_inverse = Matrix.Identity(4)
        new_child.matrix_world = temp_child.matrix_world.copy()

        if original_parent and original_parent != new_parent:
            new_parent.parent = original_parent
            new_parent.matrix_parent_inverse = Matrix.Identity(4)
            new_parent.matrix_world = temp_parent.matrix_world.copy()

        for obj, temp in zip((new_parent, new_child), (temp_parent, temp_child)):
            con = obj.constraints.new('COPY_TRANSFORMS')
            con.target = temp
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

        bpy.data.objects.remove(temp_parent)
        bpy.data.objects.remove(temp_child)

        print(f"✅ Swapped {new_parent.name} and {new_child.name} with hierarchy preserved.")
