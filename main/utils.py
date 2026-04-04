# EnipOIXth 2026


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
from math import radians as deg2rad
from math import acos
from typing import Optional
from mathutils import Vector, Euler
from bpy.types import Object, Action, PoseBone, Armature

from .. import blender_version_at_least
from . import get_hand_macro_system, HandMacroHand

from ..utils.actions import ensure_action, get_suitable_action_slots
from ..utils.animation import ensure_anim_data
from ..utils.bones import copy_bone, get_bone, put_bone, align_bone_x_axis, set_bone_parent, copy_bone_color
from ..utils.mechanism import make_constraint, make_driver, driver_var_transform, refresh_drivers
from ..utils.naming import get_name_side, Side, change_name_side
from ..utils.widgets import create_widget


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


MACRO_NAME = 'hand_macro'
MACRO_WIDGET = '''
geom.verts = [
    (0.0, 0.3285, 0.3239),
    (0.0, 0.3285, -0.3332),
    (0.0, -0.3285, 0.3239),
    (0.0, -0.3285, -0.3332),
    (0.0, 0.1792, -0.363),
    (0.0, 0.0, -0.363),
    (0.0, -0.1792, -0.363),
    (0.0, 0.3584, 0.1745),
    (0.0, 0.3584, -0.0047),
    (0.0, 0.3584, -0.1839),
    (0.0, 0.1792, 0.3537),
    (0.0, 0.0, 0.3537),
    (0.0, -0.1792, 0.3537),
    (0.0, -0.3584, 0.1745),
    (0.0, -0.3584, -0.0047),
    (0.0, -0.3584, -0.1839),
    (0.0, -0.2235, -0.3626),
    (0.0, -0.2651, -0.3593),
    (0.0, -0.301, -0.3504),
    (0.0, 0.3579, -0.2282),
    (0.0, 0.3547, -0.2697),
    (0.0, 0.3458, -0.3056),
    (0.0, -0.2235, 0.3533),
    (0.0, -0.2651, 0.35),
    (0.0, -0.301, 0.3411),
    (0.0, -0.3579, -0.2282),
    (0.0, -0.3547, -0.2697),
    (0.0, -0.3458, -0.3056),
    (0.0, 0.301, -0.3504),
    (0.0, 0.2651, -0.3593),
    (0.0, 0.2235, -0.3626),
    (0.0, 0.0896, -0.363),
    (0.0, -0.0896, -0.363),
    (0.0, 0.3458, 0.2963),
    (0.0, 0.3547, 0.2604),
    (0.0, 0.3579, 0.2189),
    (0.0, 0.3584, 0.0849),
    (0.0, 0.3584, -0.0943),
    (0.0, 0.301, 0.3411),
    (0.0, 0.2651, 0.35),
    (0.0, 0.2235, 0.3533),
    (0.0, 0.0896, 0.3537),
    (0.0, -0.0896, 0.3537),
    (0.0, -0.3458, 0.2963),
    (0.0, -0.3547, 0.2604),
    (0.0, -0.3579, 0.2189),
    (0.0, -0.3584, 0.0849),
    (0.0, -0.3584, -0.0943),
    (0.0, 0.0, 0.3537),
    (0.0, 0.0, 0.6174),
    (0.0, 0.4306, 0.0123),
    (0.0, 0.4306, -0.0216),
    (0.0, 0.556, -0.0556),
    (0.0, -0.0509, 0.5513),
    (0.0, 0.0509, 0.5513),
    (0.0, 0.556, 0.0463),
    (0.0, 0.6221, -0.0047),
    (0.0, 0.017, 0.426),
    (0.0, -0.017, 0.426),
    (0.0, -0.017, 0.5513),
    (0.0, 0.017, 0.5513),
    (0.0, 0.556, 0.0123),
    (0.0, 0.556, -0.0216),
    (0.0, 0.017, -0.4353),
    (0.0, -0.017, -0.4353),
    (0.0, -0.0509, -0.5606),
    (0.0, 0.0509, -0.5606),
    (0.0, 0.0, -0.6267),
    (0.0, 0.017, -0.5606),
    (0.0, -0.017, -0.5606),
    (0.0, -0.4306, -0.0216),
    (0.0, -0.4306, 0.0123),
    (0.0, -0.556, 0.0463),
    (0.0, -0.556, -0.0556),
    (0.0, -0.6221, -0.0047),
    (0.0, -0.556, -0.0216),
    (0.0, -0.556, 0.0123),
]
geom.edges = [
    (6, 16), (16, 17), (17, 18), (3, 18), (9, 19), (19, 20), (20, 21), (1, 21), (12, 22), (22, 23),
    (23, 24), (2, 24), (15, 25), (25, 26), (26, 27), (3, 27), (1, 28), (28, 29), (29, 30), (4, 30),
    (4, 31), (5, 31), (5, 32), (6, 32), (0, 33), (33, 34), (34, 35), (7, 35), (7, 36), (8, 36),
    (8, 37), (9, 37), (0, 38), (38, 39), (39, 40), (10, 40), (10, 41), (11, 41), (11, 42), (12, 42),
    (2, 43), (43, 44), (44, 45), (13, 45), (13, 46), (14, 46), (14, 47), (15, 47), (65, 69), (63, 68),
    (66, 67), (55, 56), (52, 62), (49, 54), (54, 60), (50, 61), (51, 62), (49, 53), (57, 58), (53, 59),
    (52, 56), (57, 60), (58, 59), (55, 61), (50, 51), (64, 69), (65, 67), (66, 68), (63, 64), (72, 76),
    (70, 75), (73, 74), (71, 76), (72, 74), (73, 75), (70, 71),
]
geom.faces = []
'''

# Each entry: (display_name, transform_channel_id)
# The transform_channel_id is the key into ACTION_TRANSFORM_MAP.
ACTION_TYPES = [
    ("Fist",       'TRANS_Y'),
    ("Extension",  'TRANS_NEGATIVE_Y'),
    ("Abduction",  'SCALE_Z'),
    ("Adduction",  'SCALE_NEGATIVE_Z'),
    ("Down",       'ROT_Y'),
    ("Up",         'ROT_NEGATIVE_Y'),
]

# Maps each transform channel to:
#   (driver_var_transform type, space, eval_time expression)
# Limits match the LIMIT_* constraints applied to the macro bone:
#   LOC_Y  → [-0.05 .. 0.05]
#   ROT_Y  → [-0.7854 .. 0.7854]  (±45°)
#   SCALE_Z → [0.5 .. 1.5], neutral = 1.0
ACTION_TRANSFORM_MAP = {
    'TRANS_Y':          ('LOC_Y',   'LOCAL', 'max(0.0, min(1.0, var / 0.05))'),
    'TRANS_NEGATIVE_Y': ('LOC_Y',   'LOCAL', 'max(0.0, min(1.0, -var / 0.05))'),
    'SCALE_Z':          ('SCALE_Z', 'LOCAL', 'max(0.0, min(1.0, (var - 1.0) / 0.5))'),
    'SCALE_NEGATIVE_Z': ('SCALE_Z', 'LOCAL', 'max(0.0, min(1.0, (1.0 - var) / 0.5))'),
    'ROT_Y':            ('ROT_Y',   'LOCAL', 'max(0.0, min(1.0, var / 0.7854))'),
    'ROT_NEGATIVE_Y':   ('ROT_Y',   'LOCAL', 'max(0.0, min(1.0, -var / 0.7854))'),
}

FK_HINTS    = ["fk", "ctrl", "ctl"]
FK_PREFIXES = ["c_", "f_", "fk_", "ctrl_"]
FILTER_OUT  = ["ref", "rot", "mch", "def", "org", "twk", "tweak", "base", "ik", "palm", "master"]
FINGER_KEYWORDS = {
    "thumb":  ["thumb", "thb", "tm"],
    "index":  ["index", "indx", "idx"],
    "middle": ["middle", "mid"],
    "ring":   ["ring"],
    "pinky":  ["pinky", "pink", "little", "lit"],
}


ARP_HAND_SELECTION_SET = {
    'hand': ['c_hand_ik', 'c_hand_fk', 'hand_ik', 'hand_fk'],   # ARP controllers + common renames
}

RIGIFY_HAND_SELECTION_SET = {
    'DEF-hand': ['hand_ik', 'hand_fk', 'ORG-hand'], # Rigify controls + _ variant for renames
}


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


def build_finger_chain(hand: "HandMacroHand"):
    """
    Build finger chains using structural data instead of names.
    Supports:
      - Multiple thumbs (via is_thumb flag)
      - No thumbs
      - Extra fingers (polydactyl) with linear interpolation from pinky
    """
    finger_chains = {}

    thumbs = []
    other_fingers = []   # non-thumb fingers in the order they appear

    for finger in hand.fingers:
        chain = [phx.bone for phx in finger.phalanges if phx.bone]
        if not chain:
            continue

        if getattr(finger, 'is_thumb', False):
            thumbs.append(chain)
        else:
            other_fingers.append(chain)

    # === Thumbs ===
    if thumbs:
        for i, chain in enumerate(thumbs):
            key = "thumb" if i == 0 else f"thumb_{i+1}"
            finger_chains[key] = chain
    else:
        # Optional: you can decide to treat the first finger as thumb-like if needed
        pass

    # === Standard fingers + extras ===
    standard_names = ["index", "middle", "ring", "pinky"]

    for i, chain in enumerate(other_fingers):
        if i < len(standard_names):
            key = standard_names[i]
        else:
            # Extra fingers beyond pinky
            extra_idx = i - len(standard_names) + 1
            key = f"extra_{extra_idx}"

        finger_chains[key] = chain

    return finger_chains


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Side detection / naming
##############################################


def is_arp_rig(arm_obj: Armature) -> bool:
    return hasattr(arm_obj.data, '["has_match_to_rig"]')


def is_rigify_rig(arm_obj: Armature) -> bool:
    return hasattr(arm_obj.data, '["rig_id"]')


def resolve_hand_root(obj: Armature, selected_name: str) -> str:
    """
    Given the bone the user has active (usually a hand control),
    return the bone whose subtree should be searched for FK finger chains.

    Works for ARP, Rigify, and custom rigs.
    Extremely tolerant of name changes in side separators, case, hyphens/underscores, and extra suffixes.
    """
    side = detect_bone_side(selected_name)
    if not side:
        return selected_name  # no side info → can't redirect reliably

    selected_lower = selected_name.lower()

    if is_arp_rig(obj):
        hand_map = ARP_HAND_SELECTION_SET
        print('--- ARP DETECTED ---')
    elif is_rigify_rig(obj):
        hand_map = RIGIFY_HAND_SELECTION_SET
        print('--- RIGIFY DETECTED ---')
    else:
        return selected_name

    for target_base, indicators in hand_map.items():
        # Does the selected bone contain any of our indicator strings?
        if any(ind.lower() in selected_lower for ind in indicators):
            # Try every realistic naming variation of the target hand bone
            target_variants = {
                target_base,
                target_base.replace('-', '_'),
                target_base.replace('_', '-'),
            }
            side_cases = [side, side.lower(), side.upper()]
            seps = ['.', '_', '-', '']

            for tv in target_variants:
                for s_case in side_cases:
                    for sep in seps:
                        candidate = tv + sep + s_case
                        if candidate in obj.pose.bones:
                            return candidate

                        # also try without trailing separator on base
                        candidate2 = tv.rstrip('._-') + sep + s_case
                        if candidate2 != candidate and candidate2 in obj.pose.bones:
                            return candidate2

            # Indicator matched but no target bone variant exists (user renamed the hand bone a lot).
            # Safest is to fall back to whatever the user actually selected.
            return selected_name

    # No indicator matched → user probably already selected the real hand bone
    return selected_name


def detect_bone_side(hand_name: str) -> str:
    """
    Infer 'L', 'R', or '' from the hand bone name.

    Delegates to naming.get_name_side() first, which handles all separator
    conventions (.L/.R, _L/_R, -L/-R via the standard split_name regex).
    Falls back to a keyword search for rigs that spell out 'left' / 'right'.
    """
    side = get_name_side(hand_name)
    if side == Side.LEFT:  return 'L'
    if side == Side.RIGHT: return 'R'

    # Keyword fallback — not covered by the regex-based side detection.
    name_lower = hand_name.lower()
    if 'left'  in name_lower: return 'L'
    if 'right' in name_lower: return 'R'
    return 'NONE'


def get_macro_bone_name(hand: str, side: str = '') -> str:
    """
    Returns the macro bone name with the correct side suffix.
    e.g. 'hand_macro.L', 'hand_macro.R', or 'hand_macro'.

    Uses naming.change_name_side to produce the suffix in the standard
    convention (.L / .R), consistent with how the rest of the rig is named.
    """
    s = side or detect_bone_side(hand)
    if s == 'L': return change_name_side(MACRO_NAME, Side.LEFT)
    if s == 'R': return change_name_side(MACRO_NAME, Side.RIGHT)
    return MACRO_NAME


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Internal helpers
##############################################


def _assign_action_for_keying(arm_obj: Armature, action: Action):
    """
    Assign action to armature animation data, handling Blender 5.0+ action slots.
    """
    anim_data = ensure_anim_data(arm_obj, create=True)
    anim_data.action = action
    if blender_version_at_least((5, 0, 0)):
        suitable = get_suitable_action_slots(arm_obj)
        if suitable:
            anim_data.action_slot = suitable[0]


def _clear_action_constraints(arm_obj: Armature, finger_chains: dict, action: Action):
    """
    Remove all ACTION constraints on every finger bone that reference the given action.
    Called before re-adding to allow non-destructive regeneration.
    """
    for bone_list in finger_chains.values():
        for entry in bone_list:
            pb = arm_obj.pose.bones[entry] if isinstance(entry, str) else entry
            for con in list(pb.constraints):
                if con.type == 'ACTION' and con.action == action:
                    pb.constraints.remove(con)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Widget
##############################################


class _Geom:
    """Simple namespace for exec-based widget geometry parsing."""
    verts: list
    edges: list
    faces: list


def get_or_create_macro_widget(arm_obj: Object, bone_name: str, widget_force_new=True) -> Object:
    """
    Get-or-create the hand macro widget and assign it to `bone_name`.

    Uses widgets.create_widget() for the collection/placement/get-or-create
    logic, then parses MACRO_WIDGET by exec-ing it into a _Geom namespace and
    passing the results to from_pydata.

    If the widget object already existed, create_widget returns None and we
    return whatever custom_shape is already assigned on the pose bone.
    If it's new, geometry is filled and the shape is assigned to the bone.
    """
    obj = create_widget(arm_obj, bone_name)

    if obj is None:
        # Widget already existed — geometry intact, nothing to do.
        return arm_obj.pose.bones[bone_name].custom_shape

    # Parse the geometry string into a _Geom instance.
    geom = _Geom()
    exec(MACRO_WIDGET, {'geom': geom})  # noqa: S102 — trusted internal constant

    obj.data.from_pydata(geom.verts, geom.edges, geom.faces)
    obj.data.update()

    pb = arm_obj.pose.bones[bone_name]
    pb.custom_shape = obj
    pb.use_custom_shape_bone_size = True

    return obj


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Macro Bone Creation
##############################################


def create_macro_bone(arm_obj: Armature, hand: str, side: str = '') -> str:
    """
    Creates the macro control bone above the hand bone.

    Non-destructive: if the bone already exists, returns its name immediately
    without touching anything. This allows re-running generate safely.

    Roll is set so local X points in world -Z ('down'), ensuring a consistent
    orientation across left and right hands regardless of how the source
    hand bone was rolled in the original rig.

    Returns the macro bone name.
    """
    macro_name = get_macro_bone_name(hand, side)

    # Non-destructive: already exists → just ensure widget and return
    if macro_name in arm_obj.data.bones:
        macro_pb = arm_obj.pose.bones[macro_name]

        # Re-apply color in case user changed the hand bone color
        hand_pb = arm_obj.pose.bones.get(hand)
        if hand_pb and hand_pb.bone.color:
            copy_bone_color(arm_obj, hand, macro_name)

        get_or_create_macro_widget(arm_obj, macro_name)
        return macro_name

    # ── EDIT mode: create bone geometry ─────────────────────────────────────
    bpy.ops.object.mode_set(mode='EDIT')

    macro = copy_bone(arm_obj, hand, macro_name, parent=False)

    eb_hand = get_bone(arm_obj, hand)
    mid = (eb_hand.head + eb_hand.tail) / 2
    pos = mid + Vector((0.0, 0.0, eb_hand.length))
    put_bone(arm_obj, macro, pos, length=eb_hand.length * 0.75)

    # Align local X to world -Z so the macro bone points 'down' consistently
    # on both left and right hands, regardless of the source bone's roll.
    align_bone_x_axis(arm_obj, macro, Vector((0.0, 0.0, -1.0)))

    set_bone_parent(arm_obj, macro, hand)

    # ── POSE mode: properties, color, widget, constraints ──────────────────
    bpy.ops.object.mode_set(mode='POSE')

    pb = get_bone(arm_obj, macro)
    pb.rotation_mode = 'XYZ'
    pb.bone.use_local_location = True

    # Lock everything except the three axes the macro actually uses.
    pb.lock_location = (True, False, True)   # Y free → Fist / Extension
    pb.lock_rotation = (True, False, True)   # Y free → Up / Down
    pb.lock_scale    = (True, True, False)   # Z free → Abduction / Adduction

    # === TRANSFER COLOR from hand bone ===
    hand_pb = arm_obj.pose.bones.get(hand)
    if hand_pb and hand_pb.bone.color:
        copy_bone_color(arm_obj, hand, macro_name)

    # === Set wire width (Blender 4.2+) ===
    if bpy.app.version >= (4, 2, 0):
        pb.custom_shape_wire_width = 2.0

    # Create / assign widget
    get_or_create_macro_widget(arm_obj, macro)

    # Transform limits — values must match the constants in ACTION_TRANSFORM_MAP.
    make_constraint(pb, 'LIMIT_LOCATION', space='LOCAL',
        use_transform_limit=True,
        min_y=-0.05, max_y=0.05,
    )
    make_constraint(pb, 'LIMIT_ROTATION', space='LOCAL',
        use_transform_limit=True,
        min_y=deg2rad(-45.0), max_y=deg2rad(45.0),
    )
    make_constraint(pb, 'LIMIT_SCALE', space='LOCAL',
        use_transform_limit=True,
        min_z=0.5, max_z=1.5,
    )

    return macro


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################
# Detection helpers
####################


def _is_valid_bone(name: str) -> bool:
    """True if the bone name does not match any filter-out keyword."""
    name_lower = name.lower()
    return not any(kw in name_lower for kw in FILTER_OUT)


def _classify_finger(name: str) -> Optional[str]:
    """Return the finger key for this bone name, or None if unrecognised."""
    name_lower = name.lower()
    for finger, keywords in FINGER_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return finger
    return None


def _has_fk_hint(name: str) -> bool:
    name_lower = name.lower()
    return (
        any(hint in name_lower for hint in FK_HINTS) or
        any(name_lower.startswith(prefix) for prefix in FK_PREFIXES)
    )


def _collect_bone_chain(root_pb: PoseBone) -> list[PoseBone]:
    """
    Collect full downward chain from root_pb, even in non-connected rigs like Rigify.
    
    Strategy:
    1. Prefer connected children (use_connect=True)
    2. Then prefer single child whose head is very close to current tail
    3. Fallback: choose the most likely continuation bone by:
       - name similarity (same prefix + incrementing number)
       - spatial proximity (closest head to current tail)
       - hierarchy level (deeper bones preferred if tied)
    """
    _CHAIN_TOLERANCE = 0.004       # increased a bit — Rigify sometimes has tiny offsets
    _NAME_NUMBER_TOL = 0.5         # allow small float differences in numeric suffix

    chain = [root_pb]
    current = root_pb

    while True:
        valid_children = [c for c in current.children if _is_valid_bone(c.name)]
        if not valid_children:
            break

        connected = [c for c in valid_children if c.bone.use_connect]
        if len(connected) == 1:
            chain.append(connected[0])
            current = connected[0]
            continue

        # Positional match
        tail_pos = Vector(current.tail)
        positional = [
            c for c in valid_children
            if (Vector(c.head) - tail_pos).length < _CHAIN_TOLERANCE
        ]
        if len(positional) == 1:
            chain.append(positional[0])
            current = positional[0]
            continue
        if len(positional) > 1:
            # Multiple candidates → prefer the one with most similar name (numeric increment)
            def name_score(child):
                curr_num = _get_numeric_suffix(current.name)
                child_num = _get_numeric_suffix(child.name)
                if curr_num is not None and child_num is not None:
                    return abs(child_num - curr_num - 1)  # want exactly +1
                dist = (Vector(child.head) - tail_pos).length
                return 1000 + dist  # fallback to distance

            best = min(positional, key=name_score)
            chain.append(best)
            current = best
            continue

        # Last resort: single non-positional child → take it (common in some custom rigs)
        if len(valid_children) == 1:
            chain.append(valid_children[0])
            current = valid_children[0]
            continue

        # Multiple children, no clear winner → stop (probably branching or helpers)
        break

    return chain


def _get_numeric_suffix(bone_name: str) -> Optional[float]:
    """Extract trailing number from bone name (e.g. 'f_index.03.L' → 3.0)"""
    import re
    m = re.search(r'(\d+(?:\.\d+)?)(?:[._-][lLrR])?$', bone_name)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _collect_subtree(pb: PoseBone) -> list[PoseBone]:
    """All descendants of pb, breadth-first, not including pb itself."""
    result = []
    queue  = list(pb.children)
    while queue:
        child = queue.pop(0)
        result.append(child)
        queue.extend(child.children)
    return result


def _finger_chain_roots(bone_pool: list[PoseBone]) -> list[PoseBone]:
    """
    From a flat pool of bones, return those whose parent is NOT also in the pool.
    These are the topmost bones of each chain within the pool.
    """
    pool_names = {pb.name for pb in bone_pool}
    return [
        pb for pb in bone_pool
        if not pb.parent or pb.parent.name not in pool_names
    ]


def _depth_to(pb: PoseBone, ancestor_name: str) -> int:
    """Steps from pb up to the named ancestor. Returns 9999 if not found."""
    depth, current = 0, pb.parent
    while current:
        if current.name == ancestor_name:
            return depth
        depth   += 1
        current  = current.parent
    return 9999


def _spatial_finger_fallback(
        unclassified_roots: list[PoseBone],
        fingers: dict[str, list],
        side: str,
):
    """
    Assign unclassified chain roots to empty finger slots by world X position.
    Right hand: descending X → thumb first.
    Left  hand: ascending  X → thumb first.
    """
    empty_slots = [k for k in ("thumb", "index", "middle", "ring", "pinky")
                   if not fingers[k]]
    if not unclassified_roots or not empty_slots:
        return

    reverse      = (side == 'R')
    sorted_roots = sorted(unclassified_roots, key=lambda pb: pb.head[0], reverse=reverse)

    for root, slot in zip(sorted_roots, empty_slots):
        fingers[slot] = _collect_bone_chain(root)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Finger detection
##############################################


def find_fk_finger_controls(arm_obj: Armature, hand: str, side: str = '') -> dict[str, list[PoseBone]]:
    """
    Discover FK finger chains anywhere in the subtree of `hand`.

    Now fully handles Rigify's MCH → FK → MCH → FK pattern.
    """
    fingers: dict[str, list[PoseBone]] = {k: [] for k in FINGER_KEYWORDS}

    # Resolve hand root (Rigify/ARP aware)
    hand_pb = get_bone(arm_obj, resolve_hand_root(arm_obj, hand))

    # Collect subtree bones
    subtree = [pb for pb in _collect_subtree(hand_pb) if _is_valid_bone(pb.name)]

    # Classify into finger pools
    finger_pools: dict[str, list[PoseBone]] = {k: [] for k in FINGER_KEYWORDS}
    unclassified: list[PoseBone] = []

    for pb in subtree:
        ft = _classify_finger(pb.name)
        if ft:
            finger_pools[ft].append(pb)
        else:
            unclassified.append(pb)

    # Prefer FK-named bones per finger 
    for ft, pool in finger_pools.items():
        if not pool:
            continue
        fk_in_pool = [pb for pb in pool if _has_fk_hint(pb.name)]
        if fk_in_pool:
            finger_pools[ft] = fk_in_pool

    # Build chains
    for ft, pool in finger_pools.items():
        if not pool:
            continue

        roots = _finger_chain_roots(pool)
        if not roots:
            continue

        # Choose shallowest root
        root = min(roots, key=lambda pb: _depth_to(pb, hand))

        # Collect all descendants of root
        # (this walks through any number of MCH bones automatically)
        def is_descendant_of(pb: PoseBone, ancestor: PoseBone) -> bool:
            current = pb.parent
            while current:
                if current == ancestor:
                    return True
                current = current.parent
            return False

        chain_bones = [pb for pb in pool if pb == root or is_descendant_of(pb, root)]

        # Sort by numeric suffix (.01, .02, .03 …)
        def get_num(pb: PoseBone) -> float:
            n = _get_numeric_suffix(pb.name)
            return n if n is not None else 9999.0

        chain_bones.sort(key=get_num)

        # Deduplicate Rigify's .001 copies (keep only one per integer number)
        seen = {}
        unique_chain = []
        for pb in chain_bones:
            num = get_num(pb)
            if num is not None:
                int_num = int(round(num))
                if int_num not in seen:
                    seen[int_num] = True
                    unique_chain.append(pb)

        fingers[ft] = unique_chain

    # Spatial fallback for unclassified bones
    unclassified_roots = _finger_chain_roots(unclassified)
    if unclassified_roots:
        _spatial_finger_fallback(unclassified_roots, fingers, side or detect_bone_side(hand))

    return fingers





###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Action creation and keyframing
##############################################


def create_hand_action(rig_name: str, action_label: str) -> Action:
    action_name = f"{rig_name} - Hand {action_label}"
    return ensure_action(action_name, create=True)


def _get_finger_value(chain_name: str, value_dict: dict, default=0.0, extra_factor: float = 1.2):
    """
    Get value for a finger.
    - Standard fingers: direct lookup
    - extra_N: linear interpolation from pinky (more extreme)
    """
    if chain_name in value_dict:
        return value_dict[chain_name]

    if chain_name.startswith("extra_"):
        try:
            extra_num = int(chain_name.split("_")[1])
            pinky_val = value_dict.get("pinky", default)
            # Linear extrapolation: each extra finger goes further in the same direction
            return pinky_val * (1.0 + (extra_num * (extra_factor - 1.0)))
        except (ValueError, IndexError):
            pass

    return default


def keyframe_procedural_hand_poses(
    action: Action, 
    arm_obj: Armature,
    action_type: str,
    finger_chains: dict[str, list],
    side: str = '',
):
    """
    Procedural hand posing that supports:
      - Multiple thumbs
      - No thumbs
      - Extra fingers (values interpolated from pinky)
    """
    _assign_action_for_keying(arm_obj, action)

    system = get_hand_macro_system(arm_obj.data)
    hand = system.hands[system.active_hand_index]
    flex_axis = hand.flexion_axis
    side_coeff = -1.0 if side.upper() == 'R' else 1.0

    # Flexion axis mapping
    axis_map = {
        'X_POS': (0,  1.0, 2, 1.0),
        'X_NEG': (0, -1.0, 2, -1.0),
        'Z_POS': (2,  1.0, 0, -1.0),
        'Z_NEG': (2, -1.0, 0, 1.0),
    }
    x_idx, x_sign, z_idx, z_sign = axis_map.get(flex_axis, (0, 1.0, 2, 1.0))

    # Base values for standard fingers
    abduction_values = {"index": 20.0, "middle": 6.0, "ring": -6.0, "pinky": -20.0}
    adduction_values = {"index": -6.0, "middle": -2.0, "ring": 6.0, "pinky": 8.0}
    up_values = {"index": -50.0, "middle": -10.0, "ring": 20.0, "pinky": 55.0}
    down_values = {"index": 50.0, "middle": 10.0, "ring": -20.0, "pinky": -55.0}

    for chain_name, bones in finger_chains.items():
        # Convert to pose bones
        pose_bones = []
        for b in bones:
            if isinstance(b, str):
                pb = arm_obj.pose.bones.get(b)
                if pb:
                    pose_bones.append(pb)
            elif hasattr(b, "name"):
                pose_bones.append(b)

        for i, pb in enumerate(pose_bones):
            pb.rotation_mode = 'XYZ'

            # Rest pose (frame 0)
            pb.rotation_euler = (0.0, 0.0, 0.0)
            pb.keyframe_insert("rotation_euler", frame=0)

            rot = [0.0, 0.0, 0.0]

            # === Action-specific posing ===
            if action_type == "Fist":
                rot[x_idx] = x_sign * deg2rad(85.0)

            elif action_type == "Extension":
                rot[x_idx] = x_sign * deg2rad(-15.0)

            elif action_type == "Abduction":
                if i == 0:  # usually only metacarpal spreads
                    spread = _get_finger_value(chain_name, abduction_values, default=0.0, extra_factor=1.3)
                    rot[z_idx] = z_sign * deg2rad(spread) * side_coeff

            elif action_type == "Adduction":
                if i == 0:
                    rz = adduction_values.get(chain_name, 0.0)
                    if chain_name.startswith("extra_"):
                        # Extrapolate the Z component further
                        rz = _get_finger_value(chain_name, {"pinky": rz}, default=rz, extra_factor=1.25)
                    rot[z_idx] = z_sign * deg2rad(rz) * side_coeff

            elif action_type == "Up":
                if i == 0:
                    lift = _get_finger_value(chain_name, up_values, default=0.0, extra_factor=1.2)
                    rot[x_idx] = x_sign * deg2rad(lift)

            elif action_type == "Down":
                if i == 0:
                    lift = _get_finger_value(chain_name, down_values, default=0.0, extra_factor=1.2)
                    rot[x_idx] = x_sign * deg2rad(lift)

            pb.rotation_euler = rot
            pb.keyframe_insert("rotation_euler", frame=10)

    # Clear residual transforms
    for bone_list in finger_chains.values():
        for entry in bone_list:
            pb = arm_obj.pose.bones.get(entry) if isinstance(entry, str) else entry
            if pb:
                pb.location = (0, 0, 0)
                pb.rotation_euler = (0, 0, 0)
                pb.scale = (1, 1, 1)

    arm_obj.animation_data.action = None


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Action constraint setup
##############################################


def create_finger_action_constraint(
        arm_obj: Armature, action: Action,
        finger_chains: dict[str, list],
        transform_type: str, macro: str,
        action_type: str,
        side: str = '',
        frame_start: int = 0, frame_end: int = 10,
):
    """
    Adds an ACTION constraint (driven by macro bone) to every finger bone.
    """
    var_type, space, expression = ACTION_TRANSFORM_MAP[transform_type]

    # === Flip sign for Right hand on Up/Down actions ===
    if side == 'R' and action_type in ("Up", "Down"):
        # Flip the sign in the expression: change -var → var  or  var → -var
        if '-var' in expression:
            expression = expression.replace('-var', 'var')
        elif 'var' in expression and '-var' not in expression:
            # Simple var → -var (handles the positive cases)
            expression = expression.replace('var', '-var')
    
    var_spec = driver_var_transform(arm_obj, macro, type=var_type, space=space)

    # Unique name for the user (visible in the constraint stack)
    con_name = f"Hand Macro {action_type}"
    if side:
        con_name += f".{side}"


    for bone_list in finger_chains.values():
        for entry in bone_list:
            pb = arm_obj.pose.bones[entry] if isinstance(entry, str) else entry

            con = make_constraint(
                pb, 'ACTION',
                name=con_name,                    
                use_eval_time=True,
                mix_mode='BEFORE_SPLIT',
                action=action,
                frame_start=frame_start,
                frame_end=frame_end,
            )

            make_driver(
                con, 'eval_time',
                expression=expression,
                variables={'var': var_spec},
            )


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Main entry point
##############################################


def generate_hand_macro(
        arm_obj: Armature,
        hand_root_bone: str,
        finger_chains: dict[str, list],
        side: str = '',
        use_shared_actions: bool = False,
) -> str:
    """
    Generate macro bone, actions and constraints for ONE hand.
    Actions are shared only if use_shared_actions=True.
    """

    side = side or detect_bone_side(hand_root_bone)

    # Create macro bone for this hand
    macro_name = create_macro_bone(arm_obj, hand_root_bone, side)

    for action_type, transform_type in ACTION_TYPES:
        # Decide action name
        if use_shared_actions:
            action_label = action_type                    # Shared: "Fist", "Up", ...
        else:
            action_label = f"{action_type}.{side}" if side else action_type

        action = create_hand_action(arm_obj.name, action_label)

        # Keyframe this hand
        keyframe_procedural_hand_poses(action, arm_obj, action_type, finger_chains, side)

        # Clear old constraints for this hand
        _clear_action_constraints(arm_obj, finger_chains, action)

        # Create constraints driven by THIS hand's macro bone
        create_finger_action_constraint(
            arm_obj, action, finger_chains, transform_type, macro_name,
            action_type, side
        )

    # Final rest pose + refresh
    if macro_name in arm_obj.pose.bones:
        macro_pb = arm_obj.pose.bones[macro_name]
        macro_pb.location = (0, 0, 0)
        macro_pb.rotation_euler = (0, 0, 0)
        macro_pb.scale = (1, 1, 1)

    bpy.context.view_layer.update()
    refresh_drivers(arm_obj)

    print(f"[HandMacro] Generated '{macro_name}'")
    return macro_name