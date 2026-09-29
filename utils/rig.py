# EnipOIXth 2025

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
## Sets of helpers when handling armatures.
###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
from typing import Any, Optional
from bpy.types import Context, Object, PoseBone, Bone, Armature
from .misc import ArmatureObject


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


def active_armature(context: Context) -> Optional[Object]:
    """Grabs the active aramature object"""
    ob = context.active_object
    return ob if ob and ob.type == 'ARMATURE' else None


def is_metarig(obj: Object) -> bool:
    """Return True if the object is a Rigify metarig."""
    return bool(
        obj and obj.type == 'ARMATURE'
        and "rig_id" not in obj.data
        and any(b.rigify_type for b in obj.pose.bones)
    )


def is_generated_rig(obj: Object) -> bool:
    """Return True if the object is a Rigify-generated rig."""
    return bool(obj and obj.type == 'ARMATURE' and "rig_id" in obj.data)


def metarig_needs_upgrade(obj: Object) -> bool:
    return bool(obj.data.get("rigify_layers"))


def is_valid_metarig(context: Context, *, allow_needs_upgrade: bool = False) -> bool:
    """Returns if a selected armature is a valid metarig (distincts if it needs upgrades or not)."""
    obj = context.object
    if not context.object:
        return False
    if obj.type != 'ARMATURE' or obj.data.get("rig_id") is not None:
        return False
    return allow_needs_upgrade or not metarig_needs_upgrade(context.object)


def find_generated_rig_from_metarig(metarig: Armature) -> Optional[ArmatureObject]:
    """Returns the generated rig for a given metarig, or None."""
    return getattr(metarig.data, "rigify_target_rig", None)


def find_metarig_from_rig(rig_obj: Object) -> Optional[Object]:
    """Find the metarig for a generated rig via direct prop or reverse lookup."""
    if not is_generated_rig(rig_obj) : return None

    # Back-link already present? If so use that.
    meta = getattr(rig_obj.data, "rigify_metarig", None)
    if meta and meta.type == 'ARMATURE':
        return meta

    # Fallback: find any metarig whose data points back to this rig (Search by rigify_target_rig).
    # Can be faulty if multiple metarigs point to the same target rig.
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and hasattr(obj.data, "rigify_target_rig"):
            try:
                if obj.data.rigify_target_rig is rig_obj:
                    return obj
            except ReferenceError:
                pass
    return None


def get_rigify_type(pose_bone: PoseBone) -> str:
    """Retrieves the rig type of a given pose bone."""
    rigify_type = pose_bone.rigify_type  # noqa
    return rigify_type.replace(" ", "")


def get_rigify_params(pose_bone: PoseBone) -> Any:
    """Retrieves the rigify parameters of a given pose bone."""
    return pose_bone.rigify_parameters  # noqa


def get_rigify_target_rig(arm: Armature) -> Optional[ArmatureObject]:
    return arm.rigify_target_rig  # noqa


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
# ------------------------------------------------------------
#   Metarig Linking / Cleanup
# ------------------------------------------------------------


def cleanup_generated_rig(rig_obj):
    """Remove metarig link properties from generated rigs."""
    if hasattr(rig_obj.data, "rigify_target_rig"):
        try:
            del rig_obj.data["rigify_target_rig"]
        except KeyError:
            pass


def ensure_backlink_from_rig(rig_obj: Object):
    """Find and store metarig on the rig if missing."""
    if not is_generated_rig(rig_obj) : return
    if getattr(rig_obj.data, "rigify_metarig", None) : return
    meta = find_metarig_from_rig(rig_obj)
    if meta:
        rig_obj.data.rigify_metarig = meta


def metarig_has_valid_target_rig(metarig_obj: Object) -> bool:
    """
    Returns True if:
      - metarig_obj is a valid Rigify metarig
      - it has a rigify_target_rig pointer
      - the target rig exists, is an armature, and is a generated rig
    """
    # Must be a valid metarig
    if not is_metarig(metarig_obj):
        return False

    m_data = metarig_obj.data

    # Must expose the rigify_target_rig pointer
    tgt = getattr(m_data, "rigify_target_rig", None)
    if not tgt:
        return False

    # Must be a generated rig (not a metarig or custom armature)
    return is_generated_rig(tgt)


def ensure_backlink_from_metarig(metarig_obj: Object):
    """If the metarig has a rigify_target_rig, write the back-link on the rig."""
    if not metarig_has_valid_target_rig(metarig_obj):
        return
    
    rig_obj = get_rigify_target_rig(metarig_obj)
    if getattr(rig_obj.data, "rigify_metarig", None) is not metarig_obj:
        rig_obj.data.rigify_metarig = metarig_obj


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


def deselect_all_pose_bones(context: Context):
    """Deselects all pose bone."""
    for pb in context.selected_pose_bones:
        pb.bone.select = False


def select_pose_bones(context: Context, bone_names: list[str] = [], active_name: str = None):
    """
    Select one or more pose bones by name, and set one as active.
    - bone_names: iterable of bone names to select
    - active_name: name of the bone to make active (must be in bone_names)
    """
    obj = context.object
    if not obj or obj.type != 'ARMATURE' or not obj.pose:
        return

    # Deselect everything first
    deselect_all_pose_bones(context)

    # Select requested bones
    for name in bone_names:
        if name in obj.pose.bones:
            obj.data.bones[name].select = True

    # Set active bone
    if not active_name or not active_name in obj.pose.bones:
        active_name = bone_names[-1]
    obj.data.bones.active = obj.data.bones[active_name]


def clear_all_pose_bone_transforms(context: Context):
    """
    Clears transforms (location, rotation, scale) from all pose bones
    of the given armature object, even if bones are hidden or unselected.
    """
    obj = context.object
    if not obj or obj.type != 'ARMATURE' or not obj.pose:
        return

    for pb in obj.pose.bones:
        # Reset location
        pb.location = (0.0, 0.0, 0.0)

        # Reset rotation (support all modes)
        if pb.rotation_mode == 'QUATERNION':
            pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        elif pb.rotation_mode == 'AXIS_ANGLE':
            pb.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        else:  # Euler
            pb.rotation_euler = (0.0, 0.0, 0.0)

        # Reset scale
        pb.scale = (1.0, 1.0, 1.0)

        # Reset basis matrix (ensures no residual transforms)
        pb.matrix_basis.identity()

    # Force depsgraph update so UI and evaluation are in sync
    context.view_layer.update()


def connected_children_names(obj: ArmatureObject, bone_name: str) -> list[str]:
    """ Returns a list of bone names (in order) of the bones that form a single
        connected chain starting with the given bone as a parent.
        If there is a connected branch, the list stops there.
    """
    bone = obj.data.bones[bone_name]
    names = []

    while True:
        connects = 0
        con_name = ""

        for child in bone.children:
            if child.use_connect:
                connects += 1
                con_name = child.name

        if connects == 1:
            names += [con_name]
            bone = obj.data.bones[con_name]
        else:
            break

    return names


def has_connected_children(bone: Bone):
    """ Returns true/false whether a bone has connected children or not.
    """
    t = False
    for b in bone.children:
        t = t or b.use_connect
    return t



