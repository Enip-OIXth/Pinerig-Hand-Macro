# SPDX-License-Identifier: GPL-3.0-or-later


"""
Rigify Action Slot Management.
"""


import bpy
from bpy.types import Action

from .rig import is_metarig
from .misc import ArmatureObject

# ------------------------------------------------------------
# Basic accessors
# ------------------------------------------------------------

def ensure_rigify_action_slots(arm: ArmatureObject):
    """Ensure the armature has rigify_action_slots and an active index."""

    arm_data = arm.data
    if not hasattr(arm_data, "rigify_action_slots"):
        return None, -1

    slots = arm_data.rigify_action_slots
    if not hasattr(arm_data, "rigify_active_action_slot"):
        arm_data.rigify_active_action_slot = 0

    return slots, arm_data.rigify_active_action_slot


def get_rigify_action_slots(arm: ArmatureObject):
    slots, _ = ensure_rigify_action_slots(arm)
    return slots


def find_slot_by_action(arm: ArmatureObject, action: Action):
    """Return (slot, index) for the slot using this action."""
    slots = get_rigify_action_slots(arm)
    for i, slot in enumerate(slots):
        if slot.action == action:
            return slot, i
    return None, -1


# ------------------------------------------------------------
# Slot creation / update
# ------------------------------------------------------------


def register_rigify_metarig_action_slot(
    metarig: ArmatureObject,
    *,
    action: Action,
    control_bone: str,
    transform_channel: str,
    frame_start: int,
    frame_end: int,
    trans_min: float,
    trans_max: float,
    symmetrical: bool = True,
):
    """Create or update a Rigify action slot on a metarig."""

    # Validate metarig
    if not is_metarig(metarig):
        return None

    slots = get_rigify_action_slots(metarig)
    if not slots:
        slots.add()

    # Map internal transform channel to Rigify enum
    RIGIFY_TRANSFORM_CHANNEL_MAP = {
        "LOC_Y": "LOCATION_Y",
        "LOC_X": "LOCATION_X",
        "LOC_Z": "LOCATION_Z",
        "ROT_Y": "ROTATION_Y",
        "ROT_X": "ROTATION_X",
        "ROT_Z": "ROTATION_Z",
        "SCALE_Z": "SCALE_Z",
        "SCALE_Y": "SCALE_Y",
        "SCALE_X": "SCALE_X",
    }

    rigify_channel = RIGIFY_TRANSFORM_CHANNEL_MAP.get(transform_channel)
    if not rigify_channel:
        print(f"[HandMacro] Unknown transform channel: {transform_channel}")
        return None

    # Check if slot already exists
    existing, idx = find_slot_by_action(metarig, action)
    slot = existing if existing else slots.add()

    slot.enabled = True
    slot.action = action
    slot.name = action.name

    slot.subtarget = control_bone
    slot.transform_channel = rigify_channel
    slot.target_space = 'LOCAL'

    slot.frame_start = frame_start
    slot.frame_end = frame_end

    slot.trans_min = trans_min
    slot.trans_max = trans_max

    slot.symmetrical = symmetrical
    slot.is_corrective = False
    slot.trigger_action_a = None
    slot.trigger_action_b = None

    metarig.data.rigify_active_action_slot = list(slots).index(slot)

    print(f"[HandMacro] Registered Rigify action slot: {action.name}")
    return slot

