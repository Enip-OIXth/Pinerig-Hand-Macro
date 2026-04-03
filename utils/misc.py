# EnipOIXth 2026

###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
import math
import collections
from abc import ABC
from mathutils import Vector, Matrix, Color
from bpy.types import Object, Armature, Mesh, ID
from itertools import tee, chain, islice, repeat, permutations
from typing import Optional, TypeVar, Sequence, TypeAlias, Callable, Generic, Iterator, Iterable, Mapping


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Lazy references
##############################################


T = TypeVar('T')
IdType = TypeVar('IdType', bound=ID)
AnyVector = Vector | Sequence[float]
Lazy: TypeAlias = T | Callable[[], T]
OptionalLazy: TypeAlias = Optional[T | Callable[[], T]]


def force_lazy(value: OptionalLazy[T]) -> T:
    """
    If the argument is callable, invokes it without arguments.
    Otherwise, returns the argument as is.
    """
    if callable(value):
        return value()
    else:
        return value


class LazyRef(Generic[T]):
    """
    Hashable lazy reference. When called, evaluates (foo, 'a', 'b'...) as foo('a','b')
    if foo is callable. Otherwise, the remaining arguments are used as attribute names or
    keys, like foo.a.b or foo.a[b] etc.
    """

    def __init__(self, first, *args):
        self.first = first
        self.args = tuple(args)
        self.first_hashable = first.__hash__ is not None

    def __repr__(self):
        return 'LazyRef{}'.format((self.first, *self.args))

    def __eq__(self, other):
        return (
            isinstance(other, LazyRef) and
            (self.first == other.first if self.first_hashable else self.first is other.first) and
            self.args == other.args
        )

    def __hash__(self):
        return (hash(self.first) if self.first_hashable
                else hash(id(self.first))) ^ hash(self.args)

    def __call__(self) -> T:
        first = self.first
        if callable(first):
            return first(*self.args)

        for item in self.args:
            if isinstance(first, (dict, list)):
                first = first[item]
            else:
                first = getattr(first, item)

        return first


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Math
##############################################


axis_vectors = {
    'x': (1, 0, 0),
    'y': (0, 1, 0),
    'z': (0, 0, 1),
    '-x': (-1, 0, 0),
    '-y': (0, -1, 0),
    '-z': (0, 0, -1),
}


# Matrices that reshuffle axis order and/or invert them
shuffle_matrix = {
    sx + x + sy + y + sz + z: Matrix((
        axis_vectors[sx + x], axis_vectors[sy + y], axis_vectors[sz + z]
    )).transposed().freeze()
    for x, y, z in permutations(['x', 'y', 'z'])
    for sx in ('', '-')
    for sy in ('', '-')
    for sz in ('', '-')
}


def angle_on_plane(plane: Vector, vec1: Vector, vec2: Vector):
    """ Return the angle between two vectors projected onto a plane.
    """
    plane.normalize()
    vec1 = vec1 - (plane * (vec1.dot(plane)))
    vec2 = vec2 - (plane * (vec2.dot(plane)))
    vec1.normalize()
    vec2.normalize()

    # Determine the angle
    angle = math.acos(max(-1.0, min(1.0, vec1.dot(vec2))))

    if angle < 0.00001:  # close enough to zero that sign doesn't matter
        return angle

    # Determine the sign of the angle
    vec3 = vec2.cross(vec1)
    vec3.normalize()
    sign = vec3.dot(plane)
    if sign >= 0:
        sign = 1
    else:
        sign = -1

    return angle * sign


# Convert between a matrix and axis+roll representations.
# Re-export the C implementation internally used by bones.
matrix_from_axis_roll = bpy.types.Bone.MatrixFromAxisRoll
axis_roll_from_matrix = bpy.types.Bone.AxisRollFromMatrix


def matrix_from_axis_pair(y_axis: AnyVector, other_axis: AnyVector, axis_name: str):
    assert axis_name in 'xz'

    y_axis = Vector(y_axis).normalized()

    if axis_name == 'x':
        z_axis = Vector(other_axis).cross(y_axis).normalized()
        x_axis = y_axis.cross(z_axis)
    else:
        x_axis = y_axis.cross(other_axis).normalized()
        z_axis = x_axis.cross(y_axis)

    return Matrix((x_axis, y_axis, z_axis)).transposed()


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Typing
##############################################


class TypedObject(Object, Generic[IdType]):
    data: IdType


ArmatureObject = TypedObject[Armature]
MeshObject = TypedObject[Mesh]


def verify_armature_obj(obj: bpy.types.Object) -> ArmatureObject:
    assert obj and obj.type == 'ARMATURE'
    return obj  # noqa


def verify_mesh_obj(obj: bpy.types.Object) -> MeshObject:
    assert obj and obj.type == 'MESH'
    return obj  # noqa


class IdPropSequence(Mapping[str, T], Sequence[T], ABC):
    def __getitem__(self, item: str | int) -> T:
        pass

    def __setitem__(self, key: str | int, value: T):
        pass

    def __iter__(self) -> Iterator[T]:
        pass

    def add(self) -> T:
        pass

    def clear(self):
        pass

    def move(self, from_idx: int, to_idx: int):
        pass

    def remove(self, item: int):
        pass


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
##############################################
# Iterators
##############################################


def padnone(iterable, pad=None):
    return chain(iterable, repeat(pad))


def pairwise_nozip(iterable):
    """s -> (s0,s1), (s1,s2), (s2,s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return a, b


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2,s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def map_list(func, *inputs):
    """[func(a0,b0...), func(a1,b1...), ...]"""
    return list(map(func, *inputs))


def skip(n, iterable):
    """Returns an iterator skipping first n elements of an iterable."""
    iterator = iter(iterable)
    if n == 1:
        next(iterator, None)
    else:
        next(islice(iterator, n, n), None)
    return iterator


def map_apply(func, *inputs):
    """Apply the function to inputs like map for side effects, discarding results."""
    collections.deque(map(func, *inputs), maxlen=0)


def find_index(sequence, item, default=None):
    for i, elem in enumerate(sequence):
        if elem == item:
            return i

    return default


def flatten_children(iterable: Iterable):
    """Enumerate the iterator items as well as their children in the tree order."""
    for item in iterable:
        yield item
        yield from flatten_children(item.children)


def flatten_parents(item):
    """Enumerate the item and all its parents."""
    while item:
        yield item
        item = item.parent


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
