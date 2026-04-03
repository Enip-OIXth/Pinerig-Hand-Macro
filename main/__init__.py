# EnipOIXth 2026


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
import importlib
from typing import List, Tuple, Type, Callable, Dict, Any, Optional
from bpy.types import Object, Context, Armature, PropertyGroup
from bpy.props import StringProperty, IntProperty, PointerProperty, EnumProperty, BoolProperty, CollectionProperty


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


FLEX_AXIS_ITEMS = [
    ('X_POS',   "+X",   "Positive X axis curls fingers (Rigify Default)"),
    ('X_NEG',   "-X",   "Negative X axis curls fingers (ARP Default)"),
    ('Z_POS',   "+Z",   "Positive Z axis curls fingers"),
    ('Z_NEG',   "-Z",   "Negative Z axis curls fingers"),
]


SIDE_ITEMS = [
    ('NONE', "None", "Side of the hand in world space."),
    ('L', "Left",  "Side of the hand in world space (+X)."),
    ('R', "Right", "Side of the hand in world space (-X)."),
]


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


loaded_submodules = []


submodules = (
    'utils',
    'operators',
    'ui',
)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


class HandMacroPhalanx(PropertyGroup):
    name: StringProperty(name="Name", default='') # "thumb_01", "thumb_02", etc.
    bone: StringProperty(name="Bone")


class HandMacroFinger(PropertyGroup):
    name: StringProperty(name="Name", default='') # "Thumb", "Index", etc.
    is_thumb : BoolProperty(name="Is Thumb", default=False, description="Check true if the finger is a thumb.")
    phalanges: CollectionProperty(type=HandMacroPhalanx)
    active_phalanx_index: IntProperty(name="Active Phalanx", default=0, min=0)

    def get_active_phalanx(self) -> Optional[HandMacroPhalanx]:
        if 0 <= self.active_phalanx_index < len(self.phalanges):
            return self.phalanges[self.active_phalanx_index]
        return None


class HandMacroHand(PropertyGroup):
    name: StringProperty(name="Name", default='') # "Hand.L", "wrist_r", etc.
    bone: StringProperty(name="Bone")
    fingers: CollectionProperty(type=HandMacroFinger)
    #side: StringProperty(name="Side", default='')
    side: EnumProperty(name="Side", items=SIDE_ITEMS, default="NONE", description="Side of the hand in world space.")
    macro_bone: StringProperty(name="Macro Bone", default='')
    flexion_axis: EnumProperty(name="Flexion Axis", items=FLEX_AXIS_ITEMS, default='X_POS', description="Axis that curls the fingers into a Fist pose.")
    active_finger_index: IntProperty(name="Active Finger", default=0, min=0)
    is_paired: BoolProperty(name="Is Paired", default=False, description="Apply the hand macro in the same call as the paired one, and merge actions.")
    # New: explicit link to the paired hand (index in system.hands)
    paired_hand_index: IntProperty(name="Paired Hand Index", default=-1, min=-1, description="Index of the symmetrical hand (-1 = none)")

    def get_active_finger(self) -> Optional[HandMacroFinger]:
        if 0 <= self.active_finger_index < len(self.fingers):
            return self.fingers[self.active_finger_index]
        return None


class HandMacroSystem(PropertyGroup): 
    hands: CollectionProperty(type=HandMacroHand) 
    active_hand_index: IntProperty(name="Active Hand", default=0, min=0)

    def get_active_hand(self) -> Optional[HandMacroHand]:
        if 0 <= self.active_hand_index < len(self.hands):
            return self.hands[self.active_hand_index]
        return None


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


#class DefaultHumanHand(HandMacroHand):
#    fingers = 


def init_default_human_hand(hand: HandMacroHand):
    """Populate a hand with the standard human finger / phalanx structure."""

    preset = [
        ("Thumb",  2, True),
        ("Index",  3, False),
        ("Middle", 3, False),
        ("Ring",   3, False),
        ("Pinky",  3, False),
    ]

    for fname, phalanx_count, is_thumb in preset:
        finger = hand.fingers.add()
        finger.name = fname
        finger.is_thumb = is_thumb
        for p_idx in range(phalanx_count):
            phx = finger.phalanges.add()
            phx.name = f"{fname}_{p_idx + 1:02d}"


def get_hand_macro_system(armature_data: Armature) -> Optional[HandMacroSystem]:
    if armature_data is None:
        return None
    return getattr(armature_data, "hand_macro_system", None)


def validate_bone_references(context) -> Tuple[bool, List[str]]:
    """
    Called before generate.
    Validate all bone references in the system.
    Returns (is_valid, list_of_error_messages)
    """
    arm_data = context.active_object.data
    system = get_hand_macro_system(arm_data)
    if not system:
        return False, ["No Hand Macro System found on this armature."]

    arm = context.object
    errors = []

    # 1. Check Hand root bones are unique and exist
    seen_roots = {}
    for i, hand in enumerate(system.hands):
        if not hand.bone:
            errors.append(f"Hand {i} ('{hand.name}') has no root bone assigned.")
            continue

        if hand.bone in seen_roots:
            errors.append(f"Duplicate hand root bone '{hand.bone}' used by Hand {i} and Hand {seen_roots[hand.bone]}.")
        else:
            seen_roots[hand.bone] = i

        if not bone_exists(arm, hand.bone):
            errors.append(f"Hand {i} ('{hand.name}') root bone '{hand.bone}' does not exist in the armature.")

    # 2. Check all phalanx bones exist
    for h_idx, hand in enumerate(system.hands):
        for f_idx, finger in enumerate(hand.fingers):
            for p_idx, phalanx in enumerate(finger.phalanges):
                if phalanx.bone and not bone_exists(arm, phalanx.bone):
                    errors.append(
                        f"Hand {h_idx} → Finger '{finger.name}' → Phalanx '{phalanx.name}' "
                        f"references non-existent bone '{phalanx.bone}'."
                    )

    is_valid = len(errors) == 0
    return is_valid, errors


def bone_exists(armature_obj: Object, bone_name: str) -> bool:
    """Fast check if bone exists."""
    if not armature_obj or not bone_name:
        return False
    return bone_name in armature_obj.pose.bones


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#------------------ REGISTRATION ------------------#
####################################################


classes = (
    HandMacroPhalanx,
    HandMacroFinger,
    HandMacroHand,
    HandMacroSystem,
)


def register_classes():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_classes():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


REGISTERED_PROPS: List[Tuple[Type, str, Callable[..., Any], Dict[str, Any]]] = [

    # Stored on Object — each armature holds its own finger assignments independently.

    #(Object, "hand_macro_phalanx", PointerProperty, {'type': HandMacroPhalanx})
    #(Object, "hand_macro_fingers", PointerProperty, {'type': HandMacroFinger}),
    (Armature, "hand_macro_system", PointerProperty, {'type': HandMacroSystem})

]


def register_properties():
    #unregister_properties() # Remove old props first (safe for reloads)

    for cls, prop_name, prop_factory, kwargs in REGISTERED_PROPS:
        setattr(cls, prop_name, prop_factory(**kwargs))


def unregister_properties():
    for cls, prop_name, *_ in REGISTERED_PROPS:
        if hasattr(cls, prop_name):
            delattr(cls, prop_name)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


def register_submodules():
    # Clear any stale entries so F8 / script-reload works correctly.
    loaded_submodules.clear()

    for name in submodules:
        mod = importlib.import_module(f"{__name__}.{name}")
        importlib.reload(mod)                   # picks up code changes without full restart
        loaded_submodules.append(mod)
        if hasattr(mod, "register"):
            mod.register()


def unregister_submodules():
    for mod in reversed(loaded_submodules):
        if hasattr(mod, "unregister"):
            mod.unregister()
    loaded_submodules.clear()


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


def register():
    register_classes()
    register_properties()
    register_submodules()


def unregister():
    unregister_submodules()
    unregister_properties()
    unregister_classes()



