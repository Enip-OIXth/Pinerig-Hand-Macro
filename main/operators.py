# EnipOIXth 2026

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
from bpy.types import Operator, Object
from bpy.props import EnumProperty, IntProperty, BoolProperty

from . import HandMacroHand, HandMacroFinger, get_hand_macro_system, validate_bone_references
from .utils import detect_hand_side, find_fk_finger_controls, generate_hand_macro, build_finger_chain
from ..utils.naming import change_name_side, Side
from ..utils.bones import get_bone


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


def clamp_active_index(collection, active_index_attr: str, container=None):
    """
    Safely clamp the active index after add/remove.
    `container` is the PropertyGroup that actually owns the active_xxx_index.
    """
    if not collection:
        if container and hasattr(container, active_index_attr):
            setattr(container, active_index_attr, 0)
        return

    max_idx = len(collection) - 1
    current = getattr(container, active_index_attr, 0) if container else 0
    clamped = max(0, min(current, max_idx))

    if clamped != current and container:
        setattr(container, active_index_attr, clamped)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
# ----------------------------------------------------------------------
# Hand Operators
# ----------------------------------------------------------------------

class HAND_MACRO_OT_add_hand(Operator):
    bl_idname = "hand_macro.add_hand"
    bl_label = "Add Hand"
    bl_description = "Add a new hand to the macro system"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)
        if not system:
            self.report({'WARNING'}, "No Hand Macro System found")
            return {'CANCELLED'}

        hand = system.hands.add()
        hand.name = "New Hand"
        
        # Set the newly added hand as active
        system.active_hand_index = len(system.hands) - 1

        # Auto-assign current active bone if possible
        if context.active_pose_bone:
            hand.bone = context.active_pose_bone.name
            hand.name = hand.bone
        return {'FINISHED'}


class HAND_MACRO_OT_remove_hand(Operator):
    bl_idname = "hand_macro.remove_hand"
    bl_label = "Remove Hand"
    bl_description = "Remove the active hand"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)
        if not system or len(system.hands) == 0:
            return {'CANCELLED'}

        # Remove the hand
        system.hands.remove(system.active_hand_index)

        # Clamp using the correct container (the system itself)
        clamp_active_index(system.hands, "active_hand_index", container=system)

        return {'FINISHED'}


# ----------------------------------------------------------------------
# Finger Operators
# ----------------------------------------------------------------------

class HAND_MACRO_OT_add_finger(Operator):
    bl_idname = "hand_macro.add_finger"
    bl_label = "Add Finger"
    bl_description = "Add a new finger to the active hand"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)
        hand = system.get_active_hand() if hasattr(system, "get_active_hand") else None

        if not hand:
            self.report({'WARNING'}, "No active hand selected")
            return {'CANCELLED'}

        finger = hand.fingers.add()
        finger.name = "New Finger"

        # Make the new finger active
        hand.active_finger_index = len(hand.fingers) - 1

        return {'FINISHED'}


class HAND_MACRO_OT_remove_finger(Operator):
    bl_idname = "hand_macro.remove_finger"
    bl_label = "Remove Finger"
    bl_description = "Remove the selected finger"
    bl_options = {'REGISTER', 'UNDO'}

    finger_index: IntProperty(default=-1)

    def execute(self, context):
        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)
        hand = system.get_active_hand()

        if not hand or not (0 <= self.finger_index < len(hand.fingers)):
            return {'CANCELLED'}

        hand.fingers.remove(self.finger_index)

        # Important: pass the hand as container!
        clamp_active_index(hand.fingers, "active_finger_index", container=hand)

        return {'FINISHED'}


# ----------------------------------------------------------------------
# Phalanx Operators
# ----------------------------------------------------------------------

class HAND_MACRO_OT_add_phalanx(Operator):
    bl_idname = "hand_macro.add_phalanx"
    bl_label = "Add Phalanx"
    bl_description = "Add a new phalanx to the active finger"
    bl_options = {'REGISTER', 'UNDO'}

    finger_index: IntProperty(default=-1)

    def execute(self, context):
        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)
        hand = system.get_active_hand() if hasattr(system, "get_active_hand") else None
        pb = context.active_pose_bone

        if not hand or not (0 <= self.finger_index < len(hand.fingers)):
            self.report({'WARNING'}, "Invalid finger")
            return {'CANCELLED'}

        finger = hand.fingers[self.finger_index]
        phalanx = finger.phalanges.add()
        phalanx.name = f"{finger.name}_{len(finger.phalanges):02d}"

        # Make new phalanx active
        finger.active_phalanx_index = len(finger.phalanges) - 1

        if pb and pb.name != hand.bone:
            phalanx.bone = pb.name

        return {'FINISHED'}


class HAND_MACRO_OT_remove_phalanx(Operator):
    bl_idname = "hand_macro.remove_phalanx"
    bl_label = "Remove Phalanx"
    bl_description = "Remove the selected phalanx"
    bl_options = {'REGISTER', 'UNDO'}

    finger_index: IntProperty(default=-1)
    phalanx_index: IntProperty(default=-1)

    def execute(self, context):
        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)
        hand = system.get_active_hand()

        if not hand or not (0 <= self.finger_index < len(hand.fingers)):
            return {'CANCELLED'}

        finger = hand.fingers[self.finger_index]

        if len(finger.phalanges) <= 1:
            self.report({'WARNING'}, "A finger must have at least one phalanx.")
            return {'CANCELLED'}

        if not (0 <= self.phalanx_index < len(finger.phalanges)):
            return {'CANCELLED'}

        finger.phalanges.remove(self.phalanx_index)

        # Pass the finger as container
        clamp_active_index(finger.phalanges, "active_phalanx_index", container=finger)

        return {'FINISHED'}


# ----------------------------------------------------------------------
# Bone Assignment
# ----------------------------------------------------------------------


class HAND_MACRO_OT_assign_phalanx_bone(Operator):
    bl_idname = "hand_macro.assign_phalanx_bone"
    bl_label = "Assign Active Bone"
    bl_description = "Assign currently active pose bone to the selected phalanx"
    bl_options = {'REGISTER', 'UNDO'}

    finger_index: IntProperty(default=-1, min=-1)
    phalanx_index: IntProperty(default=-1, min=-1)

    def execute(self, context):
        bone = context.active_pose_bone
        if not bone:
            self.report({'WARNING'}, "No active pose bone selected")
            return {'CANCELLED'}

        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)
        hand = system.get_active_hand()

        if not hand or not (0 <= self.finger_index < len(hand.fingers)):
            return {'CANCELLED'}

        finger = hand.fingers[self.finger_index]
        if not (0 <= self.phalanx_index < len(finger.phalanges)):
            return {'CANCELLED'}

        phalanx = finger.phalanges[self.phalanx_index]
        old_name = phalanx.bone
        phalanx.bone = bone.name

        self.report({'INFO'}, f"Assigned '{bone.name}' → {finger.name} phalanx")
        return {'FINISHED'}


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


class HAND_MACRO_OT_detect(Operator):
    bl_idname = "hand_macro.detect_fingers"
    bl_label = "Auto-Detect Fingers"
    bl_description = "Detect FK finger controls parented to the hand root"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object and 
                context.object.type == 'ARMATURE' and 
                context.mode == 'POSE' and 
                context.active_pose_bone is not None)

    def execute(self, context):
        arm = context.object

        arm_obj = context.active_object
        arm_data = arm_obj.data
        system = get_hand_macro_system(arm_data)
        hand = system.get_active_hand()
        hand_pb = get_bone(arm_obj, hand.bone)

        if not hand:
            self.report({'WARNING'}, "No active hand")
            return {'CANCELLED'}

        # Detect side
        side = detect_hand_side(hand_pb.name)
        hand.side = side

        detected = find_fk_finger_controls(arm, hand_pb.name, side)

        if not any(detected.values()):
            self.report({'WARNING'}, f"No finger controls found parented to '{hand_pb.name}'")
            return {'CANCELLED'}

        # Clear and rebuild
        hand.fingers.clear()

        for fname, bones in detected.items():
            if not bones:
                continue
            finger = hand.fingers.add()
            finger.name = fname.capitalize()
            finger.is_thumb = (fname.lower() == "thumb")

            for i, pb in enumerate(bones):
                ph = finger.phalanges.add()
                ph.name = f"{fname}_{i+1:02d}"
                ph.bone = pb.name

        total = sum(len(v) for v in detected.values())
        finger_count = sum(1 for v in detected.values() if v)

        side_str = f" ({side} hand)" if side else ""
        self.report({'INFO'}, f"Detected {total} bone(s) in {finger_count} finger(s){side_str}")

        # After detection, reset active indices safely
        hand.active_finger_index = 0
        if hand.fingers:
            hand.fingers[0].active_phalanx_index = 0

        return {'FINISHED'}


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


class HAND_MACRO_OT_generate(Operator):
    bl_idname = "hand_macro.generate"
    bl_label  = "Generate Hand Macro"
    bl_description = "Create the macro bone, actions, and constraints for the detected fingers"
    bl_options = {'REGISTER', 'UNDO'}
    

    @classmethod
    def poll(cls, context):
        arm_obj = context.active_object
        arm_data = arm_obj.data
        system = get_hand_macro_system(arm_data)
        hand = system.get_active_hand() if system else None
        return hand and len(hand.fingers) > 0


    def execute(self, context):
        arm_obj = context.object
        arm_data = arm_obj.data
        system = get_hand_macro_system(arm_data)
        active_hand = system.get_active_hand()
        
        if not active_hand:
            return {'CANCELLED'}
        
        valid, errors = validate_bone_references(context)
        if not valid:
            for err in errors:
                self.report({'WARNING'}, err)
            self.report({'ERROR'}, "Validation failed. Fix bone references before generating.")
            return {'CANCELLED'}
        
        # Determine if we should use shared actions
        use_shared_actions: bool = active_hand.is_paired and active_hand.paired_hand_index != -1 and active_hand.paired_hand_index != system.active_hand_index

        # === Branching logic here ===
        if use_shared_actions:
            paired_hand = system.hands[active_hand.paired_hand_index]
            self.report({'INFO'}, f"Generating paired hands with shared actions: {active_hand.name} <-> {paired_hand.name}")
            
            macro1 = self._generate_single_hand(arm_obj, active_hand, use_shared_actions=True)
            macro2 = self._generate_single_hand(arm_obj, paired_hand, use_shared_actions=True)
            
            self.report({'INFO'}, f"Generated paired macros: {macro1} + {macro2} (shared actions)")
        else:
            macro = self._generate_single_hand(arm_obj, active_hand, use_shared_actions=False)
            self.report({'INFO'}, f"Hand macro '{macro}' generated")

        return {'FINISHED'}


    def _generate_single_hand(self, arm_obj: Object, hand: HandMacroHand, use_shared_actions: bool) -> str:
        """Generate for exactly one hand. Actions may be shared or side-specific."""
        side = hand.side if hand.side != 'NONE' else detect_hand_side(hand.bone)

        # Build finger chains for this hand
        finger_chains = build_finger_chain(hand)

        # Call core function with shared flag
        macro_name = generate_hand_macro(
            arm_obj=arm_obj,
            hand_root_bone=hand.bone,
            finger_chains=finger_chains,
            side=side,
            use_shared_actions=use_shared_actions
        )

        hand.macro_bone = macro_name
        return macro_name


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


class HAND_MACRO_OT_delete_macro(Operator):
    bl_idname = "hand_macro.delete_macro"
    bl_label = "Delete Hand Macro"
    bl_description = "Completely remove the macro bone, all ACTION constraints, generated actions, and clear macro data"
    bl_options = {'REGISTER', 'UNDO'}

    confirm: BoolProperty(name="Confirm", default=False, description="Are you sure you want to delete this hand macro?")

    @classmethod
    def poll(cls, context):
        system = get_hand_macro_system(context.active_object.data)
        hand = system.get_active_hand() if system else None
        return hand and bool(hand.macro_bone)

    def invoke(self, context, event):
        """Show confirmation popup"""
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        arm_obj = context.object
        if not arm_obj or arm_obj.type != 'ARMATURE':
            return {'CANCELLED'}

        system = get_hand_macro_system(arm_obj.data)
        hand = system.get_active_hand()
        if not hand or not hand.macro_bone:
            return {'CANCELLED'}

        macro_name = hand.macro_bone
        deleted_count = 0

        # 1. Remove all ACTION constraints that belong to this macro
        for finger in hand.fingers:
            for phalanx in finger.phalanges:
                if not phalanx.bone or phalanx.bone not in arm_obj.pose.bones:
                    continue
                pb = arm_obj.pose.bones[phalanx.bone]
                for con in list(pb.constraints):
                    if con.type == 'ACTION' and con.name.startswith("Hand Macro"):
                        pb.constraints.remove(con)
                        deleted_count += 1

        # 2. Remove generated Actions for this hand macro
        action_prefix = f"{arm_obj.name} - Hand"
        side_suffix = macro_name.split('.')[-1] if '.' in macro_name else ""

        for action in list(bpy.data.actions):
            if (action.name.startswith(action_prefix) and 
                side_suffix and side_suffix in action.name):
                try:
                    bpy.data.actions.remove(action)
                    deleted_count += 1
                except:
                    pass

        # 3. Remove the macro bone
        if macro_name in arm_obj.data.bones:
            bpy.ops.object.mode_set(mode='EDIT')
            try:
                eb = arm_obj.data.edit_bones.get(macro_name)
                if eb:
                    arm_obj.data.edit_bones.remove(eb)
                    deleted_count += 1
            except Exception as e:
                print(f"Warning removing macro bone: {e}")
            finally:
                bpy.ops.object.mode_set(mode='POSE')

        # 4. Clean up system data
        hand.macro_bone = ""

        # After removing the bone, also remove the widget object if it exists
        widget_name = "WGT-" + arm_obj.name + "_" + macro_name
        widget = bpy.data.objects.get(widget_name)
        if widget:
            bpy.data.objects.remove(widget, do_unlink=True)
            deleted_count += 1
        
        # TODO: Remove invalid drivers
        

        self.report({'INFO'}, 
            f"Successfully deleted hand macro '{macro_name}' ({deleted_count} items removed)")
        
        return {'FINISHED'}
    

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


class HAND_MACRO_OT_symmetrize(Operator):
    bl_idname = "hand_macro.symmetrize"
    bl_label = "Symmetrize Hand"
    bl_description = "Create (or update) the opposite hand, mirror all bone names, and link them"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        system = get_hand_macro_system(context.active_object.data)
        return system and len(system.hands) > 0

    def execute(self, context):
        system = get_hand_macro_system(context.active_object.data)
        src = system.get_active_hand()

        if not src or src.side not in ('L', 'R'):
            self.report({'WARNING'}, "Active hand must have a valid side (L or R)")
            return {'CANCELLED'}

        dst_side = 'R' if src.side == 'L' else 'L'

        # Find or create destination hand
        dst = next((h for h in system.hands if h.side == dst_side), None)
        created = False
        if not dst:
            dst = system.hands.add()
            dst.side = dst_side
            dst.name = change_name_side(src.name, Side.RIGHT if dst_side == 'R' else Side.LEFT)
            dst.bone = change_name_side(src.bone, Side.RIGHT if dst_side == 'R' else Side.LEFT)
            created = True

        # Clear destination fingers
        dst.fingers.clear()

        # Mirror every finger + phalanx, flipping side suffix
        for f in src.fingers:
            nf = dst.fingers.add()
            nf.name = f.name
            nf.is_thumb = f.is_thumb

            for ph in f.phalanges:
                nph = nf.phalanges.add()
                nph.name = ph.name
                # Flip side on every bone name
                nph.bone = change_name_side(ph.bone, Side.RIGHT if dst_side == 'R' else Side.LEFT)

        # Link both hands bidirectionally
        src.is_paired = True
        dst.is_paired = True
        src.paired_hand_index = system.hands.find(dst.name)   # safe index lookup
        dst.paired_hand_index = system.hands.find(src.name)

        # Make sure active indices are valid
        dst.active_finger_index = 0

        status = "Created" if created else "Updated"
        self.report({'INFO'}, f"{status} symmetrical {dst_side} hand and linked both sides")
        return {'FINISHED'}


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


class HAND_MACRO_OT_move_finger(Operator):
    bl_idname = "hand_macro.move_finger"
    bl_label = "Move Finger"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')], default='UP')

    def execute(self, context):
        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)
        hand = system.get_active_hand()
        if not hand:
            return {'CANCELLED'}

        idx = hand.active_finger_index
        if self.direction == 'UP':
            new_idx = idx - 1
        else:
            new_idx = idx + 1

        if not (0 <= new_idx < len(hand.fingers)):
            return {'CANCELLED'}

        hand.fingers.move(idx, new_idx) # Actually move the item in the collection.
        hand.active_finger_index = new_idx # Update active index to follow the moved item.
        return {'FINISHED'}


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


classes = (
    HAND_MACRO_OT_add_hand,
    HAND_MACRO_OT_remove_hand,
    HAND_MACRO_OT_add_finger,
    HAND_MACRO_OT_remove_finger,
    HAND_MACRO_OT_add_phalanx,
    HAND_MACRO_OT_remove_phalanx,
    HAND_MACRO_OT_assign_phalanx_bone,
    HAND_MACRO_OT_detect,
    HAND_MACRO_OT_generate,
    HAND_MACRO_OT_delete_macro,
    HAND_MACRO_OT_symmetrize,
    HAND_MACRO_OT_move_finger,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
