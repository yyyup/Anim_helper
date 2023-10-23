import bpy

class AH_OP_Add_lights(bpy.types.Operator):
    #Add lights to the scene#

    bl_idname = "ah.add_lights"
    bl_label = "ah lights"
    bl_options = {'REGISTER', 'UNDO'}

 
    
    
    
    def execute(self, context):
        print("HERE")
        return {'FINISHED'}



#def invoke(self, context, event):
        #wm = context.window_manager
        #return wm.invoke_props_dialog(self)
