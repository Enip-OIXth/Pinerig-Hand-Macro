# EnipOIXth 2026


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
import math
from mathutils import Vector, Matrix
from typing import Optional, Iterable
from bpy.types import PoseBone, EditBone, Armature

from .misc import pairwise, ArmatureObject


##############################################
# Bone utilities
##############################################


def get_name(bone) -> Optional[str]:
    return bone.name if bone else None


def rename_bone(obj: Armature, old_name: str, new_name: str) -> str:
    """
    Rename the bone, returning the actual new name.
    """
    bone = get_bone(obj, old_name)
    bone.name = new_name
    return bone.name


def get_bone(obj: Armature, bone_name: Optional[str]) -> Optional[EditBone | PoseBone]:
    """
    Get EditBone or PoseBone by name, depending on the current mode.
    """
    if not bone_name:
        return None
    bones = obj.data.edit_bones if obj.mode == 'EDIT' else obj.pose.bones
    if bone_name not in bones:
        #raise MetarigError("bone '%s' not found" % bone_name)
        pass
    return bones[bone_name]


def new_bone(obj: Armature, bone_name: str):
    """ 
    Adds a new bone to the given armature object.
    Returns the resulting bone's name.
    """
    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        edit_bone = obj.data.edit_bones.new(bone_name)
        name = edit_bone.name
        edit_bone.head = (0, 0, 0)
        edit_bone.tail = (0, 1, 0)
        edit_bone.roll = 0
        return name
    else:
        #raise MetarigError("Cannot add new bone '%s' outside of edit mode" % bone_name)
        pass


def copy_bone(
        obj: Armature, bone_name: str, assign_name='', *,
        parent=False, inherit_scale=False, bbone=False,
        length: Optional[float] = None, scale: Optional[float] = None
    ) -> Optional[str]:
    """ 
    Makes a copy of the given bone in the given armature object.
    Returns the resulting bone's name.
    """

    if bone_name not in obj.data.edit_bones:
        print("copy_bone(): bone '%s' not found, cannot copy it" % bone_name)
        return

    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        if assign_name == '':
            assign_name = bone_name

        # Copy the edit bone
        edit_bone_1 = obj.data.edit_bones[bone_name]
        edit_bone_2 = obj.data.edit_bones.new(assign_name)
        bone_name_2 = edit_bone_2.name

        # Copy edit bone attributes
        for coll in edit_bone_1.collections:
            coll.assign(edit_bone_2)

        edit_bone_2.head = Vector(edit_bone_1.head)
        edit_bone_2.tail = Vector(edit_bone_1.tail)
        edit_bone_2.roll = edit_bone_1.roll

        if parent:
            edit_bone_2.parent = edit_bone_1.parent
            edit_bone_2.use_connect = edit_bone_1.use_connect
            edit_bone_2.use_inherit_rotation = edit_bone_1.use_inherit_rotation
            edit_bone_2.use_local_location = edit_bone_1.use_local_location

        if parent or inherit_scale:
            edit_bone_2.inherit_scale = edit_bone_1.inherit_scale

        if bbone:
            # noinspection SpellCheckingInspection
            for name in [
                'bbone_segments', 'bbone_mapping_mode',
                'bbone_easein', 'bbone_easeout',
                'bbone_rollin', 'bbone_rollout',
                'bbone_curveinx', 'bbone_curveinz', 'bbone_curveoutx', 'bbone_curveoutz',
                'bbone_scalein', 'bbone_scaleout'
            ]:
                setattr(edit_bone_2, name, getattr(edit_bone_1, name))

        # Resize the bone after copy if requested
        if length is not None:
            edit_bone_2.length = length
        elif scale is not None:
            edit_bone_2.length *= scale

        return bone_name_2
    else:
        print("Cannot copy bones outside of edit mode")
        return


def flip_bone(obj: Armature, bone_name: str):
    """ 
    Flips an edit bone.
    """
    if bone_name not in obj.data.edit_bones:
       print("flip_bone(): bone '%s' not found, cannot copy it" % bone_name)
       return

    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        bone = obj.data.edit_bones[bone_name]
        head = Vector(bone.head)
        tail = Vector(bone.tail)
        bone.tail = head + tail
        bone.head = tail
        bone.tail = head
    else:
        print("Cannot flip bones outside of edit mode")
        return


def flip_bone_chain(obj: Armature, bone_names: Iterable[str]):
    """
    Flips a connected bone chain.
    """
    assert obj.mode == 'EDIT'

    bones = [obj.data.edit_bones[name] for name in bone_names]

    # Verify chain and unparent
    for prev_bone, bone in pairwise(bones):
        assert bone.parent == prev_bone and bone.use_connect

    for bone in bones:
        bone.parent = None
        bone.use_connect = False
        for child in bone.children:
            child.use_connect = False

    # Flip bones
    for bone in bones:
        head, tail = Vector(bone.head), Vector(bone.tail)
        bone.tail = head + tail
        bone.head, bone.tail = tail, head

    # Re-parent
    for bone, next_bone in pairwise(bones):
        bone.parent = next_bone
        bone.use_connect = True


def put_bone(
        obj: Armature, bone_name: str, pos: Optional[Vector], *,
        matrix: Optional[Matrix] = None,
        length: Optional[float] = None, scale: Optional[float] = None
    ):
    """ 
    Places a bone at the given position.
    """
    if bone_name not in obj.data.edit_bones:
        print("put_bone(): bone '%s' not found, cannot move it" % bone_name)
        return

    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        bone = obj.data.edit_bones[bone_name]

        if matrix is not None:
            old_len = len(matrix)
            matrix = matrix.to_4x4()

            if pos is not None:
                matrix.translation = pos
            elif old_len < 4:
                matrix.translation = bone.head

            bone.matrix = matrix

        else:
            delta = pos - bone.head
            bone.translate(delta)

        if length is not None:
            bone.length = length
        elif scale is not None:
            bone.length *= scale
    else:
        print("Cannot 'put' bones outside of edit mode")
        return


def get_bone_parent(object: Armature, bone_name: str) -> Optional[str]:
    """
    Get the name of the parent bone, or None.
    """
    return get_name(get_bone(object, bone_name).parent)


def set_bone_parent(
        object: Armature, 
        bone_name: str, 
        parent_name: Optional[str],
        use_connect=False, 
        inherit_scale: Optional[str] = None
    ):
    """
    Set the parent of the bone.
    """
    eb = object.data.edit_bones
    bone = eb[bone_name]
    if use_connect is not None:
        bone.use_connect = use_connect
    if inherit_scale is not None:
        bone.inherit_scale = inherit_scale
    bone.parent = (eb[parent_name] if parent_name else None)


def parent_bone_chain(
        object: Armature,
        bone_names: Iterable[str],
        use_connect: Optional[bool] = None,
        inherit_scale: Optional[str] = None
    ):
    """
    Link bones into a chain with parenting. First bone may be None.
    """
    for parent, child in pairwise(bone_names):
        set_bone_parent(object, child, parent, use_connect=use_connect, inherit_scale=inherit_scale)


##############################################
# B-Bones
##############################################


def disable_bbones(obj: Armature, bone_names: Iterable[str]):
    """
    Disables B-Bone segments on the specified bones.
    """
    assert(obj.mode != 'EDIT')
    for bone in bone_names:
        obj.data.bones[bone].bbone_segments = 1


def connect_bbone_chain_handles(obj: Armature, bone_names: Iterable[str]):
    assert obj.mode == 'EDIT'

    for prev_name, next_name in pairwise(bone_names):
        prev_bone = get_bone(obj, prev_name)
        next_bone = get_bone(obj, next_name)

        prev_bone.bbone_handle_type_end = 'ABSOLUTE'
        prev_bone.bbone_custom_handle_end = next_bone

        next_bone.bbone_handle_type_start = 'ABSOLUTE'
        next_bone.bbone_custom_handle_start = prev_bone


##############################################
# Bone Roll + Orientation
##############################################


def align_bone_orientation(obj: ArmatureObject, bone_name: str, target_bone_name: str):
    """ Aligns the orientation of bone to target bone. """
    bone1_e = obj.data.edit_bones[bone_name]
    bone2_e = obj.data.edit_bones[target_bone_name]

    axis = bone2_e.y_axis.normalized() * bone1_e.length

    bone1_e.tail = bone1_e.head + axis
    bone1_e.roll = bone2_e.roll


def set_bone_orientation(obj: ArmatureObject, bone_name: str, orientation: str | Matrix):
    """ Aligns the orientation of bone to target bone or matrix. """
    if isinstance(orientation, str):
        align_bone_orientation(obj, bone_name, orientation)

    else:
        bone_e = obj.data.edit_bones[bone_name]

        matrix = Matrix(orientation).to_4x4()
        matrix.translation = bone_e.head

        bone_e.matrix = matrix


def align_bone_roll(obj: ArmatureObject, bone1: str, bone2: str):
    """ Aligns the roll of two bones.
    """
    bone1_e = obj.data.edit_bones[bone1]
    bone2_e = obj.data.edit_bones[bone2]

    bone1_e.roll = 0.0

    # Get the directions the bones are pointing in, as vectors
    y1 = bone1_e.y_axis
    x1 = bone1_e.x_axis
    y2 = bone2_e.y_axis
    x2 = bone2_e.x_axis

    # Get the shortest axis to rotate bone1 on to point in the same direction as bone2
    axis = y1.cross(y2)
    axis.normalize()

    # Angle to rotate on that shortest axis
    angle = y1.angle(y2)

    # Create rotation matrix to make bone1 point in the same direction as bone2
    rot_mat = Matrix.Rotation(angle, 3, axis)

    # Roll factor
    x3 = rot_mat @ x1
    dot = x2 @ x3
    if dot > 1.0:
        dot = 1.0
    elif dot < -1.0:
        dot = -1.0
    roll = math.acos(dot)

    # Set the roll
    bone1_e.roll = roll

    # Check if we rolled in the right direction
    x3 = rot_mat @ bone1_e.x_axis
    check = x2 @ x3

    # If not, reverse
    if check < 0.9999:
        bone1_e.roll = -roll


def align_bone_x_axis(obj: ArmatureObject, bone: str, vec: Vector):
    """ Rolls the bone to align its x-axis as closely as possible to
        the given vector.
        Must be in edit mode.
    """
    bone_e = obj.data.edit_bones[bone]

    vec = vec.cross(bone_e.y_axis)
    vec.normalize()

    dot = max(-1.0, min(1.0, bone_e.z_axis.dot(vec)))
    angle = math.acos(dot)

    bone_e.roll += angle

    dot1 = bone_e.z_axis.dot(vec)

    bone_e.roll -= angle * 2

    dot2 = bone_e.z_axis.dot(vec)

    if dot1 > dot2:
        bone_e.roll += angle * 2


def align_bone_z_axis(obj: ArmatureObject, bone: str, vec: Vector):
    """ Rolls the bone to align its z-axis as closely as possible to
        the given vector.
        Must be in edit mode.
    """
    bone_e = obj.data.edit_bones[bone]

    vec = bone_e.y_axis.cross(vec)
    vec.normalize()

    dot = max(-1.0, min(1.0, bone_e.x_axis.dot(vec)))
    angle = math.acos(dot)

    bone_e.roll += angle

    dot1 = bone_e.x_axis.dot(vec)

    bone_e.roll -= angle * 2

    dot2 = bone_e.x_axis.dot(vec)

    if dot1 > dot2:
        bone_e.roll += angle * 2


def align_bone_y_axis(obj: ArmatureObject, bone: str, vec: Vector):
    """ Matches the bone y-axis to
        the given vector.
        Must be in edit mode.
    """

    bone_e = obj.data.edit_bones[bone]
    vec.normalize()

    vec = vec * bone_e.length

    bone_e.tail = bone_e.head + vec


def compute_chain_x_axis(obj: ArmatureObject, bone_names: list[str]):
    """
    Compute the X axis of all bones to be perpendicular
    to the primary plane in which the bones lie.
    """
    eb = obj.data.edit_bones

    assert(len(bone_names) > 1)
    first_bone = eb[bone_names[0]]
    last_bone = eb[bone_names[-1]]

    # Compute normal to the plane defined by the first bone,
    # and the end of the last bone in the chain

    chain_y_axis = last_bone.tail - first_bone.head
    chain_rot_axis = first_bone.y_axis.cross(chain_y_axis)

    if chain_rot_axis.length < first_bone.length / 100:
        return first_bone.x_axis.normalized()
    else:
        return chain_rot_axis.normalized()


def align_chain_x_axis(obj: ArmatureObject, bone_names: list[str]):
    """
    Aligns the X axis of all bones to be perpendicular
    to the primary plane in which the bones lie.
    """
    chain_rot_axis = compute_chain_x_axis(obj, bone_names)

    for name in bone_names:
        align_bone_x_axis(obj, name, chain_rot_axis)


def align_bone_to_axis(
        obj: ArmatureObject, 
        bone_name: str, 
        axis: str, *,
        length: Optional[float] = None,
        roll: Optional[float] = 0.0,
        flip=False
):
    """
    Aligns the Y axis of the bone to the global axis (x,y,z,-x,-y,-z),
    optionally adjusting length and initially flipping the bone.
    """
    bone_e = obj.data.edit_bones[bone_name]

    if length is None:
        length = bone_e.length
    if roll is None:
        roll = bone_e.roll

    if axis[0] == '-':
        length = -length
        axis = axis[1:]

    vec = Vector((0, 0, 0))
    setattr(vec, axis, length)

    if flip:
        base = Vector(bone_e.tail)
        bone_e.tail = base + vec
        bone_e.head = base
    else:
        bone_e.tail = bone_e.head + vec

    bone_e.roll = roll


##############################################
# Bone Widgets
##############################################


def set_bone_widget_transform(
        obj: ArmatureObject, 
        bone_name: str,
        transform_bone: Optional[str], *,
        use_size=True, 
        scale=1.0, 
        target_size=False
):
    assert obj.mode != 'EDIT'

    bone = obj.pose.bones[bone_name]

    if transform_bone and transform_bone != bone_name:
        bone.custom_shape_transform = bone2 = obj.pose.bones[transform_bone]
        if use_size and target_size:
            scale *= bone2.length / bone.length
    else:
        bone.custom_shape_transform = None

    bone.use_custom_shape_bone_size = use_size
    bone.custom_shape_scale_xyz = (scale, scale, scale)


def copy_bone_color(obj: ArmatureObject, from_bone: str, to_bone: str):
    """Copies the color palette of the selected bone."""

    pb_1 = get_bone(obj, from_bone)
    pb_2 = get_bone(obj, to_bone)
 
    # Bone color
    pb_2.bone.color.palette = pb_1.bone.color.palette

    # Custom palette
    pb_2.bone.color.custom.normal = pb_1.bone.color.custom.normal
    pb_2.bone.color.custom.select = pb_1.bone.color.custom.select
    pb_2.bone.color.custom.active = pb_1.bone.color.custom.active

    # Pose color
    pb_2.color.palette = pb_1.color.palette