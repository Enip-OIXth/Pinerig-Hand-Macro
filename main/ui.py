# EnipOIXth 2026

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
from bpy.types import Context, UIList, Panel, UILayout

from . import HandMacroPhalanx, HandMacroFinger, HandMacroHand, HandMacroSystem, get_hand_macro_system, bone_exists
from .utils import get_macro_bone_name
from .. import blender_version_at_least

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


def draw_hand_root(context: Context, layout: UILayout, hand: "HandMacroHand"):
    """Draw the hand root bone with red alert if invalid."""

    arm_data = context.active_object.data
    system = get_hand_macro_system(arm_data)

    box = layout.box()
    box.label(text="Hand Root Bone", icon='VIEW_PAN')

    if blender_version_at_least((4, 2, 0)):
        box.separator(type='LINE')
    else:
        box.separator()

    row = box.row(align=True)
    is_valid = bone_exists(context.active_object, hand.bone)

    # Draw bone field with alert
    if not is_valid and hand.bone:
        row.alert = True

    row.prop(hand, "bone", text="")
    row.alert = False  # reset alert so it doesn't affect the whole row

    # Assign button (you can make a dedicated operator later if wanted)
    op = row.operator("hand_macro.assign_phalanx_bone", text="", icon='EYEDROPPER')
    op.finger_index = -1   # special value meaning "assign to hand root"
    op.phalanx_index = -1

    # Side and Flexion Axis
    sub = box.column()
    sub.prop(hand, "side", text="Side")
    sub.prop(hand, "flexion_axis", text="Flexion Axis")
    row = sub.row(align=True)
    row.prop(hand, "is_paired", text="Is Paired")
    if hand.is_paired:
        row.prop(hand, "paired_hand_index", text="")
    
    # === Symmetrical Status ===
    if hand.is_paired and hand.paired_hand_index >= 0:
        paired = system.hands[hand.paired_hand_index] if hand.paired_hand_index < len(system.hands) else None
        if paired:
            sub.label(text=f"Paired with: {paired.name} ({paired.side})", icon='LINKED')


def draw_finger(context: Context, layout: UILayout, finger: "HandMacroFinger", finger_idx: int):
    """Draw one finger with its phalanges and red alerts."""
    arm = context.object
    box = layout.box()

    # Finger header
    col = box.column(align=True)
    col.label(text=f"{finger.name}")

    if blender_version_at_least((4, 2, 0)):
        col.separator(type='LINE')
    else:
        col.separator()

    # Remove finger
    #op = row.operator("hand_macro.remove_finger", text="", icon="REMOVE")
    #op.finger_index = finger_idx

    # Phalanges
    ph_row = box.row(align=False)
    for j, phalanx in enumerate(finger.phalanges):
        sub = ph_row.row(align=True)

        # Bone validity check + red alert
        is_valid = bone_exists(context.active_object, phalanx.bone)

        if not is_valid and phalanx.bone:
            sub.alert = True

        sub.prop(phalanx, "bone", text="")
        sub.alert = False

        # Assign button
        op = sub.operator("hand_macro.assign_phalanx_bone", text="", icon="EYEDROPPER")
        op.finger_index = finger_idx
        op.phalanx_index = j

        # Remove phalanx button
        if len(finger.phalanges) > 1:   # prevent removing last phalanx
            op = sub.operator("hand_macro.remove_phalanx", text="", icon="X")
            op.finger_index = finger_idx
            op.phalanx_index = j

    # Add phalanx button
    op = ph_row.operator("hand_macro.add_phalanx", text="", icon="ADD")
    op.finger_index = finger_idx


def get_macro_status(context: Context, hand: "HandMacroHand") -> tuple[str, str, str]:
    """
    Returns (status_text, icon, alert_color)
    """
    if not hand.macro_bone:
        return "Not Generated", 'RADIOBUT_OFF', False

    arm = context.object
    if not arm or arm.type != 'ARMATURE':
        return "Unknown", 'QUESTION', False

    # Check if the macro bone actually exists in the armature
    if hand.macro_bone in arm.pose.bones:
        if blender_version_at_least((4, 4, 0)):
            icon = 'NODE_SOCKET_SHADER'
        else:
            icon = 'RADIOBUT_ON'
        return f"Generated: {hand.macro_bone}", icon, False
    else:
        # Macro bone name is stored but the bone was deleted
        return f"Missing: {hand.macro_bone}", 'ERROR', True


def draw_macro(context: Context, layout: UILayout, hand: "HandMacroHand"):
    """
    Draws the status of the hand macro bone.
    """
    status_text, status_icon, use_alert = get_macro_status(context, hand)

    box = layout.box()
    box.label(text="Macro Bone", icon="TRACKER")

    if blender_version_at_least((4, 2, 0)):
        box.separator(type='LINE')
    else:
        box.separator()


    row = box.row(align=True)
    if use_alert:
        row.alert = True

    row.label(text=status_text, icon=status_icon)
    row.operator("hand_macro.delete_macro", icon="X")

    row.alert = False


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


class HAND_MACRO_UL_finger_list(UIList):
    """Custom UIList for fingers."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
       
        split = layout.split(factor=0.12, align=True) 
        split.label(text=f"{index + 1}")

        row = split.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon="PMARKER_ACT")
        row.prop(item, "is_thumb", text="", icon='CHECKBOX_HLT' if item.is_thumb else 'CHECKBOX_DEHLT', emboss=False)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


class HAND_MACRO_PT_panel(Panel):
    bl_label = "Hand Macro Setup"
    bl_idname = "HAND_MACRO_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Hand Macro"


    @classmethod
    def poll(cls, context):
        return (
            context.object and
            context.object.type == 'ARMATURE' and
            context.mode == 'POSE'
        )


    def draw(self, context):
        layout = self.layout
        arm_data = context.active_object.data
        system = get_hand_macro_system(arm_data)

        if not system:
            layout.label(text="No Hand Macro System found", icon='ERROR')
            return

        # ── Hands list ───────────────────────────────────────────────────
        row = layout.row()
        row.template_list("UI_UL_list", "hand_macro_hands", system, "hands", system, "active_hand_index", rows=3)

        col = row.column(align=True)
        col.operator("hand_macro.add_hand", text="", icon="ADD")
        col.operator("hand_macro.remove_hand", text="", icon="REMOVE")

        hand = system.get_active_hand()
        if not hand:
            return
        

        layout.separator()


        # ── Hand Root Bone  ───────────────────────────────────────────────────
        draw_hand_root(context, layout, hand)
        layout.separator()


        # ── Macro Status  ───────────────────────────────────────────────────
        draw_macro(context, layout, hand)
        layout.separator()


        # ── Fingers section ───────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Fingers", icon='BONE_DATA')

        if blender_version_at_least((4, 2, 0)):
            box.separator(type='LINE')
        else:
            box.separator()

        sub = box.row()
        sub.label(text="Finger order affects macro behavior", icon='SORTSIZE')
        #box.label(text="Order determines macro generation sequence (thumb → pinky recommended)", icon='INFO')
        

        # Finger list (using template_list + custom draw for better UX)
        row = box.row()
        row.template_list("HAND_MACRO_UL_finger_list", "hand_macro_fingers", hand, "fingers", hand, "active_finger_index", rows=5)

        col = row.column(align=True)

        col.operator("hand_macro.add_finger", text="", icon="ADD")
        col.operator("hand_macro.remove_finger", text="", icon="REMOVE").finger_index = hand.active_finger_index

        col.separator()

        # Move Up / Move Down buttons
        move_up = col.operator("hand_macro.move_finger", text="", icon="TRIA_UP")
        move_up.direction = 'UP'
        move_down = col.operator("hand_macro.move_finger", text="", icon="TRIA_DOWN")
        move_down.direction = 'DOWN'

        

        # Draw detailed phalanges for the active finger
        active_finger = hand.get_active_finger()
        if active_finger:
            draw_finger(context, box, active_finger, hand.active_finger_index)


        layout.separator()


        # ── Global operators ───────────────────────────────────────────────────
        row = layout.row(align=True)
        row.operator("hand_macro.detect_fingers", icon='VIEWZOOM')
        row.operator("hand_macro.symmetrize", icon='ARROW_LEFTRIGHT')

        # Generate button
        macro_exists = bool(hand.macro_bone and hand.macro_bone in context.object.data.bones)
        gen_label = "Re-generate Hand Macro" if macro_exists else "Generate Hand Macro"
        layout.operator("hand_macro.generate", text=gen_label, icon='ARMATURE_DATA')


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#------------------ REGISTRATION ------------------#
####################################################


classes = (
    HAND_MACRO_UL_finger_list,
    HAND_MACRO_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
