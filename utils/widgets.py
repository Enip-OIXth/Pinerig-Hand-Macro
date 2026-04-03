# EnipOIXth 2026

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
import math
from typing import Optional
from bpy.types import Object, Mesh, PoseBone, Armature
from mathutils import Matrix, Euler, Vector

from .collections import ensure_collection
from .misc import ArmatureObject, MeshObject, verify_mesh_obj
from .naming import change_name_side, Side, get_name_side 


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


WGT_PREFIX = "WGT-"  # Prefix for widget objects
WGT_GROUP_PREFIX = "WGTS_"  # Prefix for the widget collection


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#------------------- Utilities --------------------#
####################################################


## COPY THIS INTO BLENDER'S SCRIPT EDITOR TO GET THE MESH DATA OF THE SELECTED OBJECT.
def object_to_widget_data(obj, add_size=False) -> str:
    """ 
    Used to transform an object into a formated string which can be used for the widgets functions.         
    """
    import bpy
    import numpy # type: ignore
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = obj.evaluated_get(depsgraph).to_mesh()
    
    def round_float(x, ndigits=4):
        # If it's extremely close to zero, return 0.0
        if abs(x) < 1e-4:
            return 0.0
        return round(float(x), ndigits)
    
    verts = []
    for v in mesh.vertices:
        co = numpy.array(tuple(v.co)) * (obj.scale[0], obj.scale[1], obj.scale[2])
        rounded = tuple(round_float(c) for c in co)
        verts.append(rounded)

    polygons = [tuple(p.vertices) for p in mesh.polygons]
    edges = [e.key for e in mesh.edges]

    wgts = [
        {"geom.verts" : verts},
        {"geom.edges" : edges},
        {"geom.faces" : polygons}, 
    ]

    def format_tuple_list(tuple_list, tab_every_new_int, v=False) -> str:
        formatted_string = ""
        for i in range(0, len(tuple_list), tab_every_new_int):
            group = tuple_list[i:i+tab_every_new_int]
            if v and add_size:
                formatted_string += "".join([f"({x[0]}, {x[1]}, {x[2]}), " for x in group]) + "\n\t"
            else:
                formatted_string += "".join([(str(item) + ', ') for item in group]) + "\n\t"
        return formatted_string
    
    def format_block(name, data, group_size=10) -> str:
        # If empty, print on one line
        if not data:
            return f"{name} = []"

        indent = " " * 4   # four spaces

        lines = [f"{name} = ["]
        count = 0

        for item in data:
            # Start a new line every group_size elements
            if count % group_size == 0:
                lines.append(f"{indent}{item},")
            else:
                lines[-1] += f" {item},"
            count += 1

        lines.append("]")
        return "\n".join(lines)
    
    verts_list_str = format_block("geom.verts", verts, group_size=1)
    edge_list_str  = format_block("geom.edges", edges, group_size=10)
    face_list_str  = format_block("geom.faces", polygons, group_size=10)
    wgts_new = f"{verts_list_str}\n{edge_list_str}\n{face_list_str}"
    
    # Print the formatted string
    print(wgts_new)
    return wgts_new

#obj = bpy.context.active_object
#object_to_widget_data(obj, add_size=True)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Widget creation
##############################################


def obj_to_bone(
        obj: Object, 
        rig: ArmatureObject, 
        bone_name: str,
        bone_transform_name: Optional[str] = None
):
    """ 
    Places an object at the location/rotation/scale of the given bone.
    """
    if bpy.context.mode == 'EDIT_ARMATURE':
        #raise MetarigError("obj_to_bone(): does not work while in edit mode")
        return

    bone = rig.pose.bones[bone_name]

    loc = bone.custom_shape_translation
    rot = bone.custom_shape_rotation_euler
    scale = Vector(bone.custom_shape_scale_xyz)

    if bone.use_custom_shape_bone_size:
        scale *= bone.length

    if bone_transform_name is not None:
        bone = rig.pose.bones[bone_transform_name]
    elif bone.custom_shape_transform:
        bone = bone.custom_shape_transform

    shape_mat = Matrix.LocRotScale(loc, Euler(rot), scale)

    obj.rotation_mode = 'XYZ'
    obj.matrix_basis = rig.matrix_world @ bone.bone.matrix_local @ shape_mat


def create_widget(
        rig: ArmatureObject,
        bone_name: str,
        bone_transform_name: Optional[str] = None,
        *,
        widget_name: Optional[str] = None,
        widget_force_new: bool = False,
        subsurf: int = 0,
) -> Optional[MeshObject]:
    """
    Creates an empty widget object for a bone, positioned at its location.

    Returns the new MeshObject so the caller can fill in geometry.
    Returns None if a widget already existed (geometry should not be re-filled).
    If widget_force_new is True, always creates a new object.

    Widget objects are placed in a hidden 'WGTS_<rig>' collection.
    """
    assert rig.mode != 'EDIT', "create_widget() cannot be called in Edit Mode"

    collection = ensure_collection(bpy.context, rig.name)
    obj_name   = widget_name or (WGT_PREFIX + rig.name + '_' + bone_name)

    if not widget_force_new:
        # Check scene objects by name; prefer non-linked copies.
        obj = bpy.context.scene.objects.get(obj_name)
        if not obj:
            local = [o for o in bpy.context.scene.objects
                     if o.name == obj_name and not o.library]
            obj   = local[0] if local else None

        if obj:
            if obj.name not in collection.objects:
                collection.objects.link(obj)
            obj_to_bone(obj, rig, bone_name, bone_transform_name)
            return None  # Geometry already present — caller must not refill.

    mesh = bpy.data.meshes.new(obj_name)
    obj  = verify_mesh_obj(bpy.data.objects.new(obj_name, mesh))
    collection.objects.link(obj)

    if subsurf > 0:
        mod        = obj.modifiers.new("subsurf", 'SUBSURF')
        mod.levels = subsurf

    obj_to_bone(obj, rig, bone_name, bone_transform_name)
    return obj


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Widget transformation
##############################################


def adjust_widget_axis(obj: Object, axis='y', offset=0.0):
    mesh = obj.data
    assert isinstance(mesh, Mesh)

    if axis[0] == '-':
        s = -1.0
        axis = axis[1]
    else:
        s = 1.0

    trans_matrix = Matrix.Translation((0.0, offset, 0.0))
    rot_matrix = Matrix.Diagonal((1.0, s, 1.0, 1.0))

    if axis == "x":
        rot_matrix = Matrix.Rotation(-s * math.pi / 2, 4, 'Z')
        trans_matrix = Matrix.Translation((offset, 0.0, 0.0))

    elif axis == "z":
        rot_matrix = Matrix.Rotation(s * math.pi / 2, 4, 'X')
        trans_matrix = Matrix.Translation((0.0, 0.0, offset))

    matrix = trans_matrix @ rot_matrix

    for vert in mesh.vertices:
        vert.co = matrix @ vert.co


def adjust_widget_transform_mesh(obj: Optional[Object], matrix: Matrix, local: bool | None = None):
    """
    Adjust the generated widget by applying a correction matrix to the mesh.
    local=True     → matrix is in the widget's own local space.
    local=False    → matrix is in world space.
    local=PoseBone → matrix is in that bone's local space.
    """
    if obj:
        mesh = obj.data
        assert isinstance(mesh, Mesh)

        if local is not True:
            if local:
                assert isinstance(local, PoseBone)
                bone_mat = local.id_data.matrix_world @ local.bone.matrix_local
                matrix = bone_mat @ matrix @ bone_mat.inverted()

            obj_mat = obj.matrix_basis
            matrix = obj_mat.inverted() @ matrix @ obj_mat

        mesh.transform(matrix)
    

def _transform_widget(
        geom, 
        head_tail = 0.0, 
        offset = Vector((0.0, 0.0, 0.0)), 
        rotation = Vector((0.0, 0.0, 0.0)), 
        size = 1.0, 
        scale = Vector((1.0, 1.0, 1.0))
):
    center = Vector((0, head_tail, 0))
    # **Position adjustment: Interpolate between head & tail**
    geom.verts = [center + offset + Vector((x, y, z)) for x, y, z in geom.verts]

    # Apply size to each vertex
    geom.verts = [(x * size, y * size, z * size) for x, y, z in geom.verts]

    # Apply scaling to each vertex
    geom.verts = [(x * scale.x, y * scale.y, z * scale.z) for x, y, z in geom.verts]
    
    # Apply Euler rotation (converted to a matrix)
    rot_matrix = Euler(rotation).to_matrix()
    geom.verts = [(rot_matrix @ Vector((x, y, z))) for x, y, z in geom.verts]


def set_wigdet_wire_width(obj : ArmatureObject, bone_name : str, width : float = 1.0):
    if bpy.app.version < (4, 2, 0):
        return
    bone = obj.pose.bones[bone_name]
    bone.custom_shape_wire_width = width