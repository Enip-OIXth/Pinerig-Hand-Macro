# EnipOIXth 2025

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
# Helpers to handle actions / action slots...
###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
from bpy_extras import anim_utils
from typing import Optional, Tuple
from bpy.props import CollectionProperty
from bpy.types import Object, Action, AnimData, Context

from .animation import ensure_anim_data, get_fcurves

try:
    from bpy.types import ActionSlot
except ImportError:
    ActionSlot = None


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#--------------------- ACTION  --------------------#
####################################################


def ensure_action(action_name: str, create: bool = False) -> Optional[Action]:
	"""
	Ensures the action exists, creates it if needed.
	"""
	action = bpy.data.actions.get(action_name, None)
	if not action and create:
		action = bpy.data.actions.new(action_name)
	return action


def link_action_to_object(obj: Object, action_name: str):
	"""
	Links the action to the designated object.
	"""
	action = ensure_action(action_name)
	if not action: 
		return

	anim_data = ensure_anim_data(obj, create=True)
	anim_data.action = action


def unlink_action_from_object(obj: Object):
	"""Unlinks currently selected action from the designated object."""
	anim_data = ensure_anim_data(obj)
	if not anim_data:
		return
	anim_data.action = None


def action_has_any_keyframes(action: Action, exclude_names: list[str], frame: int, action_slot: 'ActionSlot' = None) -> bool:
	"""
	Checks if an action has any keyframe (fcurves) in its data.
	Can exclude a list of target names from the search.
	Works across Blender versions.
	"""

	# Any fcurve keyed for an object (not in excluded_names) at this frame?
	for fc in get_fcurves(action, action_slot):
		grp = fc.group
		if not grp or grp.name in exclude_names:
			continue

		# Check if a keyframe point exactly at 'frame'
		if any(int(kp.co[0]) == int(frame) for kp in fc.keyframe_points):
			return True
		
	return False


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#------------------ ACTION SLOTS ------------------#
####################################################


def remove_action_slot(action: Action, slot: ActionSlot):
	"""
	Removes a given action slot.
	Includes all animation that is associated with that slot
	"""
	action.slots.remove(slot)


def create_action_slot(action: Action, slot_name: str, id_type: str = 'OBJECT'):
	"""
	Creates a new action slot.
	Does not make it active in the action.
	"""
	action.slots.new(id_type, slot_name)


def get_suitable_action_slots(obj: Object) -> Optional[CollectionProperty]: # of ActionSlots
	"""The list of valid slots in this animation data-block."""
	anim_data = ensure_anim_data(obj)
	if not anim_data:
		return None
	return anim_data.action_suitable_slots


def assign_action_slot(obj: Object, slot: ActionSlot):
	"""
	Assigns the action slot.
	"""
	if slot not in get_suitable_action_slots(obj): 
		return
	anim_data = ensure_anim_data(obj)
	anim_data.action_slot = slot


def unassign_action_slot(obj: Object):
	"""
	Unassigns the action slot.
	"""
	anim_data = ensure_anim_data(obj)
	anim_data.action_slot = None


def get_action_slot_id(slot: ActionSlot) -> str:
	"""
	This is the display name, prefixed by two characters determined by the slot's ID type.
	Used when selecting a slot via bpy.data.actions['Action'].slots['slot_id'].
	"""
	return slot.identifier


def set_action_slot_name(slot: ActionSlot, name: str):
	slot.name_display = name


def get_action_slot_name(slot: ActionSlot) -> str:
	return slot.name_display


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
