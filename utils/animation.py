# EnipOIXth 2025

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
# Helpers to handle animation data / fcurves / keyframes...
###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
from bpy_extras import anim_utils
from typing import Optional, Tuple
from bpy.props import CollectionProperty
from bpy.types import Context, Object, Action, AnimData, PoseBone

from .. import blender_version_at_least

try:
    from bpy.types import ActionSlot
except ImportError:
    ActionSlot = None


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#--------------------- SCENE ----------------------#
####################################################


def get_current_scene_frame(context: Context):
    """Grabs the current scene frame."""
    return context.scene.frame_current


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#---------------- ANIMATION DATA ------------------#
####################################################


def ensure_anim_data(obj: Object, create: bool = False) -> Optional[AnimData]:
	"""
	Ensures animation data exists for the given object.
	"""
	if not obj.animation_data and create:
		obj.animation_data_create() # Blender function.
	return obj.animation_data


def clear_anim_data(obj: Object):
	"""Clears any animation data from the object."""
	obj.animation_data_clear() # Blender function.
	

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#--------------------- FCURVES --------------------#
####################################################


def get_fcurves(action: Action, action_slot: 'ActionSlot'= None):
	"""
	Return the fcurves container for an Action, cross-version.
	Blender < 5.0  → action.fcurves
	Blender >= 5.0 → channelbag.fcurves for the given slot
	"""
	if not blender_version_at_least((5, 0, 0)):
		return action.fcurves
	
	if action_slot is None:
		action_slot = action.slots[0] if action.slots else None
	if action_slot is None:
		raise RuntimeError("No ActionSlot available for this Action in Blender 5.0+")
	channelbag = anim_utils.action_ensure_channelbag_for_slot(action, action_slot)
	return channelbag.fcurves


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#-------------------- KEYFRAMES -------------------#
####################################################


def is_keyframe_selected(kp):
    """
    Cross-version keyframe selection check.
    Blender < 5.0  → use kp.select_control_point
    Blender >= 5.0 → use kp.select
    """
    if blender_version_at_least((5, 0, 0)):
        return getattr(kp, "select", False)
    else:
        return getattr(kp, "select_control_point", False)


def collect_selected_frames(action: Action, action_slot: 'ActionSlot'= None):
    """
	Return frames that have selected keyframes in the Dope Sheet/Graph Editor.
	"""
    return {
		int(kp.co[0]) 
        for fc in get_fcurves(action, action_slot) 
        for kp in fc.keyframe_points if is_keyframe_selected(kp)
	}


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
