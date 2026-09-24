#!/usr/bin/env python3

"""Shared type parameters and ordering protocol.

Use ``T`` for an element with no more specific role, ``KeyT`` for ordered
keys, and ``ValueT`` for stored values or aggregates of the same type.
Use ``AggregateT`` when an aggregate differs from the stored value type,
and ``ActionT`` for updates applied to values. ``StateT`` describes a search
state; ``StateT_contra`` is its contravariant counterpart for consumers.
``VertexValueT`` and ``EdgeValueT`` describe graph payloads, while ``PointT``
and ``PathT`` describe tree-DP cluster values. These are type parameters,
not nominal identifiers such as the graph's ``Node`` and ``EdgeNum``.
"""

from typing import TypeVar, Protocol

T = TypeVar('T')
ValueT = TypeVar('ValueT')
AggregateT = TypeVar('AggregateT')
ActionT = TypeVar('ActionT')
StateT = TypeVar('StateT')
StateT_contra = TypeVar('StateT_contra', contravariant=True)
VertexValueT = TypeVar('VertexValueT')
EdgeValueT = TypeVar('EdgeValueT')
PointT = TypeVar('PointT')
PathT = TypeVar('PathT')

KeyT = TypeVar('KeyT', bound='Comparable')


class Comparable(Protocol):
    """
    Protocol for types that define a strict weak ordering.

    Any type implementing this protocol must provide ``__lt__``. That is
    enough for generic code that only needs to compare values or sort them.

    Examples:
        A custom key type can implement ``Comparable`` and then be used with
        algorithms that require orderability.

    This protocol is intentionally minimal so generic containers can accept a
    wide range of user-defined ordered types.
    It matches the expectations of the sorting and ordered-set utilities in cplib.
    """
    def __lt__(self: KeyT, other: KeyT, /) -> bool: ...
