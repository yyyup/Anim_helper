import bpy
import re

class AH_AutoProcessor:
    _instance = None
    _is_running = False
    _processed_actions = set()
    _timer = None
    _rig = None
    _check_interval = 2.0
    _auto_cleanup = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AH_AutoProcessor, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def reset(self):
        self._is_running = False
        self._processed_actions.clear()
        self._timer = None
        self._rig = None

auto_processor = AH_AutoProcessor()

class FacialAnimationProcessor:
    BODY_MESH_BASE_NAME = "CC_Base_Body"
    
    KEEP_BONES = {
        "jaw", "jaw.L", "jaw.R", "eye.L", "eye.R", "eyes",
        "lip.B", "lip.T", "lips.L", "lips.R",
        "brow.T.L", "brow.T.R", "nose", "chin", "tongue", "head"
    }
    
    def has_rigify_bones(self, action):
        if not action.fcurves:
            return False
        
        if any(keyword in action.name.lower() for keyword in ['rigify', '_rig']):
            return True
        
        for fcurve in list(action.fcurves)[:10]:
            bone_name = self.extract_bone_name_from_fcurve(fcurve.data_path)
            if bone_name and bone_name.startswith('CC_Base_'):
                return False
            elif bone_name and bone_name in self.KEEP_BONES:
                return True
        
        return True

    def find_body_mesh_in_children(self, rig):
        for child in rig.children:
            if child.type == 'MESH' and child.name.startswith(self.BODY_MESH_BASE_NAME):
                if child.data.shape_keys:
                    return child, None
        return None, "No CC_Base_Body mesh found"
    
    def filter_rig_action_bones(self, rig_action):
        if not rig_action or not rig_action.fcurves:
            return 0
        
        fcurves_to_remove = []
        kept_bones = set()
        removed_bones = set()
        
        for fcurve in rig_action.fcurves:
            bone_name = self.extract_bone_name_from_fcurve(fcurve.data_path)
            if bone_name:
                # Simple logic: Only keep explicitly facial bones
                if (bone_name in self.KEEP_BONES or 
                    any(term in bone_name.lower() for term in ['jaw', 'eye', 'lip', 'brow', 'nose', 'chin', 'tongue', 'head'])):
                    kept_bones.add(bone_name)
                else:
                    fcurves_to_remove.append(fcurve)
                    removed_bones.add(bone_name)
        
        for fcurve in fcurves_to_remove:
            rig_action.fcurves.remove(fcurve)
        
        print(f"Kept {len(kept_bones)} facial bones, removed {len(removed_bones)} body bones")
        return len(fcurves_to_remove)
    
    def extract_bone_name_from_fcurve(self, data_path):
        pattern = r'pose\.bones\["([^"]+)"\]'
        match = re.search(pattern, data_path)
        return match.group(1) if match else None

    def generate_auto_names(self, rig_name):
        letters_only = ''.join(c for c in rig_name if c.isalpha())
        char_code = letters_only[:3].upper()
        if len(char_code) < 3:
            char_code = char_code.ljust(3, 'X')
        
        rig_pattern = f"CC_{char_code}_RA_SPEECH_"
        shapekey_pattern = f"CC_{char_code}_SA_SPEECH_"
        
        highest_num = 0
        for action in bpy.data.actions:
            for pattern in [rig_pattern, shapekey_pattern]:
                if action.name.startswith(pattern):
                    suffix = action.name[len(pattern):]
                    if suffix.isdigit():
                        highest_num = max(highest_num, int(suffix))
        
        next_num = highest_num + 1
        rig_action_name = f"{rig_pattern}{next_num:02d}"
        shapekey_action_name = f"{shapekey_pattern}{next_num:02d}"
        
        return rig_action_name, shapekey_action_name

    def auto_process_single_animation(self, rig, rig_action, shapekey_action):
        try:
            # Filter bones
            removed_count = self.filter_rig_action_bones(rig_action)

            # Find body mesh
            body_mesh, error_msg = self.find_body_mesh_in_children(rig)
            if not body_mesh:
                print(f"Error: {error_msg}")
                return False

            # Generate names
            rig_action_name, shapekey_action_name = self.generate_auto_names(rig.name)

            # Rename actions
            old_rig_name = rig_action.name
            old_shapekey_name = shapekey_action.name
            rig_action.name = rig_action_name
            shapekey_action.name = shapekey_action_name

            # Push to NLA
            if not rig.animation_data:
                rig.animation_data_create()
            
            rig_track = rig.animation_data.nla_tracks.new()
            rig_track.name = f"Facial Rig - {rig_action.name}"
            rig_track.strips.new(rig_action.name, int(rig_action.frame_range[0]), rig_action)

            if not body_mesh.data.shape_keys.animation_data:
                body_mesh.data.shape_keys.animation_data_create()
            
            shape_track = body_mesh.data.shape_keys.animation_data.nla_tracks.new()
            shape_track.name = f"Facial Shapes - {shapekey_action.name}"
            shape_track.strips.new(shapekey_action.name, int(shapekey_action.frame_range[0]), shapekey_action)

            # Cleanup extra actions
            if auto_processor._auto_cleanup:
                deleted_count = self.cleanup_extra_actions(rig_action, shapekey_action)
                print(f"Deleted {deleted_count} extra actions")

            print(f"Success: {old_rig_name} -> {rig_action_name}")
            print(f"Success: {old_shapekey_name} -> {shapekey_action_name}")
            
            return True
            
        except Exception as e:
            print(f"Processing error: {str(e)}")
            return False

    def cleanup_extra_actions(self, rig_action, shapekey_action):
        # Extract motion ID from rig action name
        motion_id_pattern = r'\|(\d+)_TempMotion$'
        match = re.search(motion_id_pattern, rig_action.name)
        if not match:
            return 0
        
        motion_id = match.group(1)
        character_prefix = rig_action.name.split('|')[0]
        
        # Find all actions from same session
        actions_to_delete = []
        for action in bpy.data.actions:
            if f"|{motion_id}_TempMotion" in action.name and action.name.startswith(character_prefix):
                # Skip main actions
                if action == rig_action or action == shapekey_action:
                    continue
                # Skip renamed actions
                if not action.name.endswith("_TempMotion"):
                    continue
                # Skip main rig and body actions
                if "|A|" in action.name or "|K|Body|" in action.name:
                    continue
                
                actions_to_delete.append(action)
        
        # Delete extra actions
        deleted_count = 0
        for action in actions_to_delete:
            try:
                print(f"Deleting: {action.name}")
                bpy.data.actions.remove(action)
                deleted_count += 1
            except:
                pass
        
        return deleted_count

    def is_retargeted_action(self, action):
        return ('_TempMotion' in action.name and 
                '|A|' in action.name and 
                not action.name.startswith(('ott_', 'CC_Base')))
    
    def find_corresponding_shapekey_action(self, rig_action):
        motion_id_pattern = r'\|(\d+)_TempMotion$'
        match = re.search(motion_id_pattern, rig_action.name)
        if not match:
            return None
        
        motion_id = match.group(1)
        character_prefix = rig_action.name.split('|')[0]
        shapekey_name = f"{character_prefix}|K|Body|{motion_id}_TempMotion"
        return bpy.data.actions.get(shapekey_name)


class AH_StartAutoProcessing(bpy.types.Operator):
    bl_idname = "object.start_auto_processing"
    bl_label = "Start Auto-Processing"
    bl_description = "Start monitoring for retargeted animations"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if auto_processor._is_running:
            self.report({'WARNING'}, "Already running!")
            return {'CANCELLED'}
        
        if not context.object or context.object.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature first!")
            return {'CANCELLED'}
        
        auto_processor._rig = context.object
        auto_processor._is_running = True
        auto_processor._processed_actions.clear()
        
        auto_processor._timer = context.window_manager.event_timer_add(2.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        self.report({'INFO'}, f"Auto-processing started for {context.object.name}")
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if event.type in {'ESC'} and event.value == 'PRESS':
            self.stop_processing(context)
            return {'FINISHED'}
        
        if event.type == 'TIMER' and auto_processor._is_running:
            self.check_for_new_actions(context)
        
        if not auto_processor._is_running:
            self.stop_processing(context)
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def stop_processing(self, context):
        if auto_processor._timer:
            context.window_manager.event_timer_remove(auto_processor._timer)
            auto_processor._timer = None
        auto_processor._is_running = False
    
    def check_for_new_actions(self, context):
        processor = FacialAnimationProcessor()
        
        for action in bpy.data.actions:
            if ('_TempMotion' in action.name and '|A|' in action.name and 
                action.name not in auto_processor._processed_actions and
                not action.name.startswith(('ott_', 'CC_Base'))):
                
                if processor.has_rigify_bones(action):
                    shapekey_action = processor.find_corresponding_shapekey_action(action)
                    if shapekey_action:
                        success = processor.auto_process_single_animation(auto_processor._rig, action, shapekey_action)
                        if success:
                            auto_processor._processed_actions.add(action.name)


class AH_StopAutoProcessing(bpy.types.Operator):
    bl_idname = "object.stop_auto_processing" 
    bl_label = "Stop Auto-Processing"
    bl_description = "Stop monitoring"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if auto_processor._timer:
            context.window_manager.event_timer_remove(auto_processor._timer)
            auto_processor._timer = None
        
        auto_processor._is_running = False
        self.report({'INFO'}, "Auto-processing stopped")
        return {'FINISHED'}


class AH_AutoFacialProcessor(bpy.types.Operator):
    bl_idname = "object.auto_facial_processor"
    bl_label = "Process Current Animation"
    bl_description = "Manually process current retargeted animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        processor = FacialAnimationProcessor()
        
        # Find retargeted action
        for action in bpy.data.actions:
            if processor.is_retargeted_action(action) and processor.has_rigify_bones(action):
                shapekey_action = processor.find_corresponding_shapekey_action(action)
                if shapekey_action:
                    success = processor.auto_process_single_animation(context.object, action, shapekey_action)
                    if success:
                        self.report({'INFO'}, "Animation processed successfully!")
                        return {'FINISHED'}
        
        self.report({'ERROR'}, "No retargeted actions found")
        return {'CANCELLED'}


class AH_ToggleAutoCleanup(bpy.types.Operator):
    bl_idname = "object.toggle_auto_cleanup"
    bl_label = "Toggle Auto Cleanup"
    bl_description = "Enable/disable cleanup"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        auto_processor._auto_cleanup = not auto_processor._auto_cleanup
        status = "enabled" if auto_processor._auto_cleanup else "disabled"
        self.report({'INFO'}, f"Auto-cleanup {status}")
        return {'FINISHED'}


class AH_ClearProcessedActions(bpy.types.Operator):
    bl_idname = "object.clear_processed_actions"
    bl_label = "Clear Processed List"
    bl_description = "Clear processed actions list"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        count = len(auto_processor._processed_actions)
        auto_processor._processed_actions.clear()
        self.report({'INFO'}, f"Cleared {count} processed actions")
        return {'FINISHED'}