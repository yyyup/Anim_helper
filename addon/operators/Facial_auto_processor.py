import bpy
import re
from bpy.app.handlers import persistent

class AH_AutoProcessor:
    """Singleton class to manage the auto-processing state"""
    _instance = None
    _is_running = False
    _processed_actions = set()
    _timer = None
    _rig = None
    _check_interval = 2.0  # Check every 2 seconds
    _auto_cleanup = True  # Enable automatic cleanup by default
    
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
        """Reset the processor state"""
        self._is_running = False
        self._processed_actions.clear()
        self._timer = None
        self._rig = None
        # Keep _auto_cleanup setting

# Global auto-processor instance
auto_processor = AH_AutoProcessor()

class FacialAnimationProcessor:
    """Core processing logic separated from Blender operators"""
    
    # Body mesh name for Character Creator
    BODY_MESH_BASE_NAME = "CC_Base_Body"
    
    # Facial bones to KEEP (preserve keyframes) - ONLY Rigify bones
    KEEP_BONES = {
        "brow.T.L.001", "brow.T.L.002", "brow.T.L.003", "brow.T.R.001", "brow.T.R.002", "brow.T.R.003",
        "cheek.B.L.001", "cheek.B.R.001", "chin", "lid.B.L.002", "lid.B.R.002", "lid.T.L.002", "lid.T.R.002",
        "lip.B", "lip.B.L.001", "lip.B.R.001", "lip.T", "lip.T.L.001", "lip.T.R.001", "lips.L", "lips.R",
        "nose.002", "nose.L.001", "nose.R.001", "ear.L", "ear.R", "eye.L", "eye.R", "eyes",
        "jaw_master", "master_eye.L", "master_eye.R", "nose_master", "teeth.B", "teeth.T", "tongue_master",
        "brow.B.L", "brow.B.L.001", "brow.B.L.002", "brow.B.L.003", "brow.B.L.004",
        "brow.B.R", "brow.B.R.001", "brow.B.R.002", "brow.B.R.003", "brow.B.R.004",
        "brow.T.L", "brow.T.R", "cheek.T.L.001", "cheek.T.R.001", "chin.001", "chin.002", "chin.L", "chin.R",
        "ear.L.002", "ear.L.003", "ear.L.004", "ear.R.002", "ear.R.003", "ear.R.004",
        "jaw", "jaw.L", "jaw.L.001", "jaw.R", "jaw.R.001",
        "lid.B.L", "lid.B.L.001", "lid.B.L.003", "lid.B.R", "lid.B.R.001", "lid.B.R.003",
        "lid.T.L", "lid.T.L.001", "lid.T.L.003", "lid.T.R", "lid.T.R.001", "lid.T.R.003",
        "nose", "nose.001", "nose.003", "nose.004", "nose.005", "nose.L", "nose.R",
        "tongue", "tongue.001", "tongue.002", "tongue.003", "head"
    }
    
    def has_rigify_bones(self, action):
        """Check if action contains Rigify bones (not CC_Base bones)"""
        if not action.fcurves:
            return False
        
        # First check - if action name contains a Rigify rig name, it's likely Rigify
        if any(keyword in action.name.lower() for keyword in ['rigify', '_rig', 'metarig']):
            print(f"🔍 Action {action.name} detected as Rigify based on name")
            return True
        
        # Sample F-curves to check bone types
        rigify_bone_count = 0
        cc_base_bone_count = 0
        total_checked = 0
        
        for fcurve in list(action.fcurves)[:20]:  # Check more curves for accuracy
            bone_name = self.extract_bone_name_from_fcurve(fcurve.data_path)
            if bone_name:
                total_checked += 1
                if bone_name.startswith('CC_Base_'):
                    cc_base_bone_count += 1
                elif bone_name in self.KEEP_BONES:
                    rigify_bone_count += 1
                # Also check for common Rigify naming patterns
                elif any(pattern in bone_name.lower() for pattern in ['.l', '.r', 'def-', 'mch-', 'org-']):
                    rigify_bone_count += 1
        
        print(f"🔍 Action {action.name}: {rigify_bone_count} Rigify bones, {cc_base_bone_count} CC_Base bones (checked {total_checked} total)")
        
        # If we found CC_Base bones, it's definitely CC_Base
        if cc_base_bone_count > 0:
            return False
            
        # If we found Rigify bones or patterns, it's Rigify
        if rigify_bone_count > 0:
            return True
            
        # If no specific bones found but action has facial-related data paths, assume it's valid
        facial_data_paths = 0
        for fcurve in list(action.fcurves)[:10]:
            if any(facial_term in fcurve.data_path.lower() for facial_term in ['jaw', 'eye', 'lip', 'brow', 'nose', 'tongue']):
                facial_data_paths += 1
        
        if facial_data_paths > 0:
            print(f"🔍 Action {action.name} has {facial_data_paths} facial data paths - assuming Rigify")
            return True
            
        return False

    def find_body_mesh_in_children(self, rig):
        """Find the body mesh among the children of the selected armature"""
        mesh_candidates = []
        
        for child in rig.children:
            if child.type == 'MESH' and self.mesh_name_matches(child.name):
                if child.data.shape_keys:
                    mesh_candidates.append(child)
        
        if not mesh_candidates:
            return None, f"No mesh child named '{self.BODY_MESH_BASE_NAME}' with shapekeys found"
        
        # Prefer exact name match, then first alphabetically
        mesh_candidates.sort(key=lambda x: (x.name != self.BODY_MESH_BASE_NAME, x.name))
        return mesh_candidates[0], None
    
    def mesh_name_matches(self, mesh_name):
        """Check if mesh name matches the base pattern"""
        if mesh_name == self.BODY_MESH_BASE_NAME:
            return True
        pattern = rf"^{re.escape(self.BODY_MESH_BASE_NAME)}\.(\d{{3}})$"
        return bool(re.match(pattern, mesh_name))
    
    def filter_rig_action_bones(self, rig_action):
        """Keep only facial bones, delete everything else"""
        if not rig_action or not rig_action.fcurves:
            return 0
        
        fcurves_to_remove = []
        kept_bones = set()
        removed_bones = set()
        
        print(f"🔍 Filtering bones in action: {rig_action.name}")
        print(f"🔍 Total F-curves: {len(rig_action.fcurves)}")
        
        for fcurve in rig_action.fcurves:
            bone_name = self.extract_bone_name_from_fcurve(fcurve.data_path)
            if bone_name:
                # Check if this is a facial bone
                is_facial_bone = False
                
                # Method 1: Direct match with KEEP_BONES
                if bone_name in self.KEEP_BONES:
                    is_facial_bone = True
                
                # Method 2: Check for facial keywords in bone names
                elif any(facial_term in bone_name.lower() for facial_term in 
                        ['jaw', 'eye', 'lid', 'brow', 'lip', 'nose', 'tongue', 
                         'chin', 'cheek', 'ear', 'teeth', 'master_eye', 'face']):
                    is_facial_bone = True
                    print(f"🔍 Bone {bone_name} identified as facial by keyword")
                
                # Method 3: Skip obvious body parts
                elif any(body_term in bone_name.lower() for body_term in 
                        ['spine', 'shoulder', 'arm', 'hand', 'finger', 'thumb',
                         'leg', 'foot', 'toe', 'hip', 'thigh', 'shin', 'forearm',
                         'upper_arm', 'chest', 'pelvis', 'torso']):
                    is_facial_bone = False
                    print(f"🔍 Bone {bone_name} identified as body part - removing")
                
                # Method 4: For Rigify, check DEF- bones that might be facial
                elif bone_name.startswith('DEF-') and any(facial_term in bone_name.lower() for facial_term in 
                        ['jaw', 'eye', 'lid', 'brow', 'lip', 'nose', 'tongue', 'chin', 'cheek', 'ear', 'head']):
                    is_facial_bone = True
                    print(f"🔍 DEF bone {bone_name} identified as facial")
                
                if is_facial_bone:
                    kept_bones.add(bone_name)
                else:
                    fcurves_to_remove.append(fcurve)
                    removed_bones.add(bone_name)
        
        # Remove non-facial F-curves
        for fcurve in fcurves_to_remove:
            rig_action.fcurves.remove(fcurve)
        
        print(f"✅ Filtered: kept {len(kept_bones)} facial bones, removed {len(removed_bones)} other bones")
        print(f"🔍 Kept bones: {sorted(list(kept_bones))[:10]}...")  # Show first 10
        print(f"🔍 Removed bones: {sorted(list(removed_bones))[:10]}...")  # Show first 10
        
        return len(fcurves_to_remove)
    
    def extract_bone_name_from_fcurve(self, data_path):
        """Extract bone name from F-curve data path"""
        pattern = r'pose\.bones\["([^"]+)"\]'
        match = re.search(pattern, data_path)
        return match.group(1) if match else None

    def generate_auto_names(self, rig_name):
        """Generate automatic action names based on rig name"""
        # Extract first 3 letters from rig name
        letters_only = ''.join(c for c in rig_name if c.isalpha())
        char_code = letters_only[:3].upper()
        
        if len(char_code) < 3:
            char_code = char_code.ljust(3, 'X')
        
        rig_pattern = f"CC_{char_code}_RA_SPEECH_"
        shapekey_pattern = f"CC_{char_code}_SA_SPEECH_"
        
        highest_num = self.find_highest_action_number(rig_pattern, shapekey_pattern)
        next_num = highest_num + 1
        
        rig_action_name = f"{rig_pattern}{next_num:02d}"
        shapekey_action_name = f"{shapekey_pattern}{next_num:02d}"
        
        return rig_action_name, shapekey_action_name
    
    def find_highest_action_number(self, rig_pattern, shapekey_pattern):
        """Find the highest existing action number for this character"""
        highest = 0
        
        for action in bpy.data.actions:
            for pattern in [rig_pattern, shapekey_pattern]:
                if action.name.startswith(pattern):
                    suffix = action.name[len(pattern):]
                    if suffix.isdigit():
                        highest = max(highest, int(suffix))
        
        return highest

    def auto_process_single_animation(self, rig, rig_action, shapekey_action):
        """Process a single rig/shapekey action pair (for auto-processing)"""
        try:
            # Backup original active actions
            original_rig_action = rig.animation_data.action if rig.animation_data else None
            original_shapekey_action = None
            
            # Set rig action as active temporarily
            if not rig.animation_data:
                rig.animation_data_create()
            rig.animation_data.action = rig_action
            
            # Filter rig action (remove body bones, keep facial)
            removed_count = self.filter_rig_action_bones(rig_action)

            # Find body mesh
            body_mesh, error_msg = self.find_body_mesh_in_children(rig)
            if not body_mesh:
                print(f"❌ {error_msg}")
                return False

            # Backup and set shapekey action as active temporarily
            if body_mesh.data.shape_keys.animation_data:
                original_shapekey_action = body_mesh.data.shape_keys.animation_data.action
            else:
                body_mesh.data.shape_keys.animation_data_create()
            
            body_mesh.data.shape_keys.animation_data.action = shapekey_action

            # Generate names
            rig_action_name, shapekey_action_name = self.generate_auto_names(rig.name)

            # Rename actions
            old_rig_name = rig_action.name
            old_shapekey_name = shapekey_action.name
            rig_action.name = rig_action_name
            shapekey_action.name = shapekey_action_name

            # Push to NLA tracks
            try:
                # Push rig action to NLA
                rig_nla_track = rig.animation_data.nla_tracks.new()
                rig_nla_track.name = f"Facial Rig - {rig_action.name}"
                rig_strip = rig_nla_track.strips.new(
                    rig_action.name, 
                    int(rig_action.frame_range[0]), 
                    rig_action
                )

                # Push shapekey action to NLA
                shapekey_nla_track = body_mesh.data.shape_keys.animation_data.nla_tracks.new()
                shapekey_nla_track.name = f"Facial Shapes - {shapekey_action.name}"
                shapekey_strip = shapekey_nla_track.strips.new(
                    shapekey_action.name, 
                    int(shapekey_action.frame_range[0]), 
                    shapekey_action
                )
                
                print(f"✅ Pushed to NLA: {rig_action_name} & {shapekey_action_name}")
                
            except Exception as e:
                print(f"❌ Error pushing to NLA: {str(e)}")
                return False

            # Clear active actions (they're now in NLA)
            rig.animation_data.action = original_rig_action
            body_mesh.data.shape_keys.animation_data.action = original_shapekey_action

            # Clean up unnecessary retargeted actions from the same motion (if enabled)
            deleted_count = 0
            if auto_processor._auto_cleanup:
                deleted_count = self.cleanup_unnecessary_retargeted_actions(rig_action, shapekey_action)
            else:
                print("🔧 Auto-cleanup disabled - skipping deletion of extra retargeted actions")

            print(f"✅ Auto-processed: {old_rig_name} → {rig_action_name}")
            print(f"✅               {old_shapekey_name} → {shapekey_action_name}")
            print(f"   Removed {removed_count} non-facial F-curves")
            if auto_processor._auto_cleanup:
                print(f"   Deleted {deleted_count} unnecessary retargeted actions")
            
            return True
            
        except Exception as e:
            print(f"❌ Auto-processing error: {str(e)}")
            return False

    def is_retargeted_action(self, action):
        """Check if action looks like a retargeted action"""
        # Must have TempMotion and |A| pattern
        has_temp_motion = '_TempMotion' in action.name
        has_rig_marker = '|A|' in action.name
        
        # Should NOT start with original CC4 prefixes (these are source actions)
        is_original_cc4 = action.name.startswith(('ott_', 'CC_Base'))
        
        # Debug output
        print(f"🔍 Checking action: {action.name}")
        print(f"    - Has _TempMotion: {has_temp_motion}")
        print(f"    - Has |A| marker: {has_rig_marker}")
        print(f"    - Is original CC4: {is_original_cc4}")
        
        result = has_temp_motion and has_rig_marker and not is_original_cc4
        print(f"    - Is retargeted: {result}")
        
        return result
    
    def find_corresponding_shapekey_action(self, rig_action):
        """Find the shapekey action that corresponds to the rig action"""
        # Extract the ID from the rig action name
        match = re.search(r'\|(\d+)_TempMotion$', rig_action.name)
        if not match:
            return None
        
        motion_id = match.group(1)
        character_prefix = rig_action.name.split('|')[0]
        
        # Look for corresponding shapekey action
        shapekey_name = f"{character_prefix}|K|Body|{motion_id}_TempMotion"
        return bpy.data.actions.get(shapekey_name)

    def cleanup_unnecessary_retargeted_actions(self, rig_action, shapekey_action):
        """Clean up unnecessary retargeted actions after processing main facial animations"""
        try:
            # Extract motion ID and character prefix from the processed actions
            match = re.search(r'\|(\d+)_TempMotion$', rig_action.name)
            if not match:
                print("⚠️ Could not extract motion ID for cleanup")
                return 0
            
            motion_id = match.group(1)
            character_prefix = rig_action.name.split('|')[0]
            
            print(f"🧹 Starting cleanup for motion ID: {motion_id}, character: {character_prefix}")
            
            # Find all actions that match this motion ID and character but are NOT the main ones
            actions_to_delete = []
            
            for action in bpy.data.actions:
                # Check if this action belongs to the same retargeting session
                if (f"|{motion_id}_TempMotion" in action.name and 
                    action.name.startswith(character_prefix)):
                    
                    # Skip the main rig and body shapekey actions we just processed
                    if action == rig_action or action == shapekey_action:
                        continue
                    
                    # Skip if it's the renamed version of our processed actions
                    if not action.name.endswith("_TempMotion"):
                        continue
                    
                    # Check if it's one of the extra retargeted actions we want to delete
                    # These typically have patterns like |K|TearLine|, |K|Tongue|, |K|Eye|, etc.
                    if ("|K|" in action.name and "|K|Body|" not in action.name) or \
                       any(extra_type in action.name for extra_type in ["|K|TearLine|", "|K|Tongue|", "|K|Eye|", 
                                                                        "|K|Hat|", "|K|Sword|", "|K|Hair|", "|K|Cloth|"]):
                        actions_to_delete.append(action)
                        print(f"🗑️ Marking for deletion: {action.name}")
            
            # Safety check - make sure none of these actions are currently active
            for obj in bpy.data.objects:
                if obj.animation_data and obj.animation_data.action in actions_to_delete:
                    print(f"⚠️ Skipping deletion of {obj.animation_data.action.name} - currently active on {obj.name}")
                    actions_to_delete.remove(obj.animation_data.action)
            
            # Delete the unnecessary actions
            deleted_count = 0
            for action in actions_to_delete:
                try:
                    print(f"🗑️ Deleting: {action.name}")
                    bpy.data.actions.remove(action)
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Failed to delete {action.name}: {str(e)}")
            
            print(f"✅ Cleanup complete: Deleted {deleted_count} unnecessary retargeted actions")
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error during cleanup: {str(e)}")
            return 0


class AH_StartAutoProcessing(bpy.types.Operator):
    """Start automatic processing of retargeted facial animations"""
    bl_idname = "object.start_auto_processing"
    bl_label = "Start Auto-Processing"
    bl_description = "Start monitoring for retargeted animations and process them automatically"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if auto_processor._is_running:
            self.report({'WARNING'}, "Auto-processing is already running!")
            return {'CANCELLED'}
        
        # Ensure a rig is selected
        if not context.object or context.object.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select an armature object first!")
            return {'CANCELLED'}
        
        # Validate that the rig has children (looking for body mesh)
        body_mesh_found = False
        for child in context.object.children:
            if child.type == 'MESH' and self.mesh_name_matches(child.name):
                if child.data.shape_keys:
                    body_mesh_found = True
                    break
        
        if not body_mesh_found:
            self.report({'WARNING'}, f"No CC_Base_Body mesh with shapekeys found as child of {context.object.name}. Continuing anyway...")
        
        # Start the auto-processing
        auto_processor._rig = context.object
        auto_processor._is_running = True
        auto_processor._processed_actions.clear()
        
        # Start the timer
        auto_processor._timer = context.window_manager.event_timer_add(
            auto_processor._check_interval, 
            window=context.window
        )
        context.window_manager.modal_handler_add(self)
        
        self.report({'INFO'}, f"🔄 Auto-processing started for rig '{context.object.name}'. Just retarget your animations!")
        return {'RUNNING_MODAL'}
    
    def mesh_name_matches(self, mesh_name):
        """Check if mesh name matches CC_Base_Body pattern"""
        if mesh_name == "CC_Base_Body":
            return True
        pattern = r"^CC_Base_Body\.(\d{3})$"
        return bool(re.match(pattern, mesh_name))
    
    def modal(self, context, event):
        # Handle ESC key to stop processing
        if event.type in {'ESC'} and event.value == 'PRESS':
            self.stop_processing(context)
            self.report({'INFO'}, "Auto-processing stopped by user")
            return {'FINISHED'}
        
        if event.type == 'TIMER' and auto_processor._is_running:
            try:
                print(f"⏰ Auto-processor timer check - {len(auto_processor._processed_actions)} processed so far")
                # Check for new retargeted actions
                self.check_and_process_retargeted_actions(context)
            except Exception as e:
                print(f"❌ Auto-processing error: {str(e)}")
                import traceback
                traceback.print_exc()
                self.report({'ERROR'}, f"Auto-processing error: {str(e)}")
        
        if not auto_processor._is_running:
            # Stop the timer and exit modal
            self.stop_processing(context)
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def stop_processing(self, context):
        """Clean up timer and stop processing"""
        if auto_processor._timer:
            context.window_manager.event_timer_remove(auto_processor._timer)
            auto_processor._timer = None
        auto_processor._is_running = False
    
    def check_and_process_retargeted_actions(self, context):
        """Check for new retargeted actions and process them"""
        if not auto_processor._rig:
            return
        
        processor = FacialAnimationProcessor()
        
        # Debug: Print all actions to see what we have
        print(f"🔍 Checking {len(bpy.data.actions)} total actions...")
        
        # Find all current actions that look like retargeted actions
        retargeted_actions = []
        for action in bpy.data.actions:
            # Debug: Check each action
            if '_TempMotion' in action.name and '|A|' in action.name:
                print(f"🔍 Found TempMotion action: {action.name}")
                
                if action.name not in auto_processor._processed_actions:
                    print(f"🔍 Action {action.name} not yet processed")
                    
                    if processor.is_retargeted_action(action):
                        print(f"🔍 Action {action.name} matches retargeted pattern")
                        
                        # Check if this action has Rigify bones (not CC_Base bones)
                        if processor.has_rigify_bones(action):
                            print(f"✅ Action {action.name} confirmed as Rigify - adding to process list")
                            retargeted_actions.append(action)
                        else:
                            print(f"❌ Action {action.name} not detected as Rigify")
                    else:
                        print(f"❌ Action {action.name} doesn't match retargeted pattern")
                else:
                    print(f"⏭️ Action {action.name} already processed")
        
        print(f"🎯 Found {len(retargeted_actions)} new retargeted actions to process")
        
        # Process each new retargeted action
        for rig_action in retargeted_actions:
            print(f"🔄 Auto-detected new retargeted action: {rig_action.name}")
            
            # Find corresponding shapekey action
            shapekey_action = processor.find_corresponding_shapekey_action(rig_action)
            
            if shapekey_action:
                print(f"✅ Found corresponding shapekey action: {shapekey_action.name}")
                success = processor.auto_process_single_animation(
                    auto_processor._rig, rig_action, shapekey_action
                )
                if success:
                    # Mark as processed
                    auto_processor._processed_actions.add(rig_action.name)
                    print(f"✅ Auto-processed successfully: {rig_action.name}")
                else:
                    print(f"❌ Auto-processing failed for: {rig_action.name}")
            else:
                print(f"⚠️ Could not find corresponding shapekey action for: {rig_action.name}")
                # Let's debug what shapekey actions exist
                shapekey_actions = [a.name for a in bpy.data.actions if '|K|Body|' in a.name and '_TempMotion' in a.name]
                print(f"🔍 Available shapekey actions: {shapekey_actions}")
                
                # Try to find the pattern anyway
                match = re.search(r'\|(\d+)_TempMotion$', rig_action.name)
                if match:
                    motion_id = match.group(1)
                    print(f"🔍 Looking for motion ID: {motion_id}")
                    character_prefix = rig_action.name.split('|')[0]
                    expected_name = f"{character_prefix}|K|Body|{motion_id}_TempMotion"
                    print(f"🔍 Expected shapekey name: {expected_name}")
                else:
                    print(f"❌ Could not extract motion ID from: {rig_action.name}")


class AH_StopAutoProcessing(bpy.types.Operator):
    """Stop automatic processing of retargeted facial animations"""
    bl_idname = "object.stop_auto_processing" 
    bl_label = "Stop Auto-Processing"
    bl_description = "Stop monitoring for retargeted animations"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if not auto_processor._is_running:
            self.report({'WARNING'}, "Auto-processing is not running!")
            return {'CANCELLED'}
        
        # Stop the timer if it exists
        if auto_processor._timer:
            context.window_manager.event_timer_remove(auto_processor._timer)
            auto_processor._timer = None
        
        processed_count = len(auto_processor._processed_actions)
        auto_processor._is_running = False
        
        self.report({'INFO'}, f"🛑 Auto-processing stopped. Processed {processed_count} animations.")
        return {'FINISHED'}


class AH_AutoFacialProcessor(bpy.types.Operator):
    """Process retargeted facial animations and organize them to NLA tracks"""
    bl_idname = "object.auto_facial_processor"
    bl_label = "Auto Facial Animation Processor"
    bl_description = "Automatically process current retargeted facial animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Manual processing - find and process current retargeted animation"""
        try:
            rig = context.object

            # Ensure a rig is selected
            if rig is None or rig.type != 'ARMATURE':
                self.report({'ERROR'}, "No rig selected. Please select an armature object and try again.")
                return {'CANCELLED'}

            processor = FacialAnimationProcessor()

            # Find current retargeted action
            retargeted_rig_action = None
            retargeted_shapekey_action = None
            
            for action in bpy.data.actions:
                if (processor.is_retargeted_action(action) and 
                    processor.has_rigify_bones(action)):
                    
                    retargeted_rig_action = action
                    # Find corresponding shapekey action
                    retargeted_shapekey_action = processor.find_corresponding_shapekey_action(action)
                    break
            
            if not retargeted_rig_action:
                self.report({'ERROR'}, "No retargeted rig actions found. Please retarget an animation first.")
                return {'CANCELLED'}
                
            if not retargeted_shapekey_action:
                self.report({'ERROR'}, f"Found rig action '{retargeted_rig_action.name}' but no corresponding shapekey action.")
                return {'CANCELLED'}
            
            success = processor.auto_process_single_animation(
                rig, retargeted_rig_action, retargeted_shapekey_action
            )
            
            if success:
                self.report({'INFO'}, "✅ Animation processed successfully and pushed to NLA!")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "❌ Processing failed. Check console for details.")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error during processing: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return self.execute(context)


class AH_ToggleAutoCleanup(bpy.types.Operator):
    """Toggle automatic cleanup of unnecessary retargeted actions"""
    bl_idname = "object.toggle_auto_cleanup"
    bl_label = "Toggle Auto Cleanup"
    bl_description = "Enable/disable automatic cleanup of extra retargeted actions"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        auto_processor._auto_cleanup = not auto_processor._auto_cleanup
        status = "enabled" if auto_processor._auto_cleanup else "disabled"
        self.report({'INFO'}, f"Auto-cleanup {status}")
        return {'FINISHED'}


class AH_ClearProcessedActions(bpy.types.Operator):
    """Clear the list of processed actions to allow reprocessing"""
    bl_idname = "object.clear_processed_actions"
    bl_label = "Clear Processed List"
    bl_description = "Clear the list of processed actions (useful for reprocessing)"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        count = len(auto_processor._processed_actions)
        auto_processor._processed_actions.clear()
        self.report({'INFO'}, f"Cleared {count} processed actions from memory")
        return {'FINISHED'}