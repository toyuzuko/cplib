#!/usr/bin/env python3

from __future__ import annotations

import random
import sys
from collections.abc import Iterable, Iterator, Mapping, MutableMapping, MutableSet, Set
from reprlib import recursive_repr
from typing import TypeVar, overload

from cplib.tools.type import ValueT

OtherValueT = TypeVar('OtherValueT')
_INTEGER_HASH_LIMIT = sys.hash_info.modulus


def _encode_integer(key: object, mask: int) -> int | bytes:
    if not isinstance(key, int):
        raise TypeError('keys must be integers')
    masked = key ^ mask
    if -_INTEGER_HASH_LIMIT < masked < _INTEGER_HASH_LIMIT:
        return masked
    return masked.to_bytes((masked.bit_length() + 8) // 8, 'little', signed=True)


def _decode_integer(key: int | bytes, mask: int) -> int:
    return (key if isinstance(key, int) else int.from_bytes(key, 'little', signed=True)) ^ mask


class SafeIntegerDict(MutableMapping[int, ValueT]):
    """Dictionary with collision-resistant storage for integer keys.

    XOR-masked keys with absolute value below sys.hash_info.modulus are stored
    as integers: their hashes equal their values except that -1 hashes to -2.
    Larger keys are reversibly encoded as bytes to use the interpreter's
    randomized bytes hash. XOR alone cannot prevent collisions between large
    integers with identical low bits. Iteration,
    mapping views, comparisons and updates expose the original integers.
    Insertion order is preserved. This is a MutableMapping, not a dict subclass.

    Intended for contest inputs independent of the interpreter's hash seed;
    it does not guarantee worst-case constant time against adaptive inputs.
    Keep hash randomization enabled and do not publish its seed. For a key
    occupying B bytes, encoding and hashing take O(B) time and space. The
    usual average O(1) operation bounds assume bounded-size integer keys.
    Converting to a built-in dict restores ordinary integer hashing.

    Attributes:
        b: Random XOR mask; do not change it after construction.

    Space Complexity:
        O(n) for n bounded-size keys, excluding stored values.

    Examples:
        >>> d = SafeIntegerDict[int]()
        >>> d.update({10: 3, 20: 4})
        >>> list(d.items())
        [(10, 3), (20, 4)]
    """

    def __init__(self, values: Mapping[int, ValueT] | Iterable[tuple[int, ValueT]] = ()) -> None:
        """Initialize from a mapping or key-value pairs.

        Args:
            values: Initial integer keys and values; later duplicates win.

        Returns:
            None.

        Time Complexity:
            Average O(n) for n input entries.
        """
        self.b = random.getrandbits(30)
        self._data: dict[int | bytes, ValueT] = {}
        self.update(values)

    def __getitem__(self, key: int) -> ValueT:
        """Return a stored value in average O(1) time.

        Args:
            key: Integer key.

        Returns:
            The value associated with key.

        Raises:
            KeyError: If key is absent.
        """
        encoded = _encode_integer(key, self.b)
        try:
            return self._data[encoded]
        except KeyError:
            raise KeyError(key) from None

    def __setitem__(self, key: int, value: ValueT) -> None:
        """Store a value in average O(1) time.

        Args:
            key: Integer key.
            value: Value to store.

        Returns:
            None.
        """
        self._data[_encode_integer(key, self.b)] = value

    @overload
    def get(self, key: int) -> ValueT | None: ...

    @overload
    def get(self, key: int, default: ValueT) -> ValueT: ...

    @overload
    def get(self, key: int, default: OtherValueT) -> ValueT | OtherValueT: ...

    def get(self, key: int, default: OtherValueT | None = None) -> ValueT | OtherValueT | None:
        """Look up a key without raising KeyError in average O(1) time.

        Args:
            key: Integer key.
            default: Value returned when the key is absent; defaults to None.

        Returns:
            The stored value, or default if the key is absent.
        """
        return self._data.get(_encode_integer(key, self.b), default)

    def __delitem__(self, key: int) -> None:
        """Delete an entry in average O(1) time.

        Args:
            key: Integer key.

        Returns:
            None.

        Raises:
            KeyError: If key is absent.
        """
        encoded = _encode_integer(key, self.b)
        try:
            del self._data[encoded]
        except KeyError:
            raise KeyError(key) from None

    def __contains__(self, key: object) -> bool:
        """Test membership in average O(1) time.

        Args:
            key: Candidate key.

        Returns:
            Whether key is an integer stored in the dictionary.
        """
        return isinstance(key, int) and _encode_integer(key, self.b) in self._data

    def __iter__(self) -> Iterator[int]:
        """Iterate over original keys in insertion order in O(n) total time.

        Returns:
            An iterator over integer keys.
        """
        mask = self.b
        return (_decode_integer(key, mask) for key in self._data)

    def __reversed__(self) -> Iterator[int]:
        """Iterate over keys in reverse insertion order in O(n) total time.

        Returns:
            An iterator over integer keys.
        """
        mask = self.b
        return (_decode_integer(key, mask) for key in reversed(self._data))

    def __len__(self) -> int:
        """Return the entry count in O(1) time.

        Returns:
            Number of stored keys.
        """
        return len(self._data)

    def clear(self) -> None:
        """Remove all entries in O(n) time.

        Returns:
            None.
        """
        self._data.clear()

    def popitem(self) -> tuple[int, ValueT]:
        """Remove the last inserted entry in average O(1) time.

        Returns:
            The original integer key and its value.

        Raises:
            KeyError: If the dictionary is empty.
        """
        key, value = self._data.popitem()
        return _decode_integer(key, self.b), value

    def copy(self) -> SafeIntegerDict[ValueT]:
        """Return a shallow copy in O(n) time.

        Returns:
            An independent dictionary sharing the stored values.
        """
        result = SafeIntegerDict[ValueT]()
        result.b = self.b
        result._data = self._data.copy()
        return result

    def __copy__(self) -> SafeIntegerDict[ValueT]:
        """Implement copy.copy in O(n) time.

        Returns:
            An independent dictionary sharing the stored values.
        """
        return self.copy()

    @classmethod
    @overload
    def fromkeys(cls, iterable: Iterable[int]) -> SafeIntegerDict[None]: ...

    @classmethod
    @overload
    def fromkeys(cls, iterable: Iterable[int], value: OtherValueT) -> SafeIntegerDict[OtherValueT]: ...

    @classmethod
    def fromkeys(cls, iterable: Iterable[int], value: OtherValueT | None = None) -> SafeIntegerDict[OtherValueT] | SafeIntegerDict[None]:
        """Construct a dictionary with one shared value in average O(n) time.

        Args:
            iterable: Initial integer keys.
            value: Value stored for every key; defaults to None.

        Returns:
            A new dictionary containing the supplied keys.
        """
        if value is None:
            return SafeIntegerDict[None]((key, None) for key in iterable)
        return SafeIntegerDict[OtherValueT]((key, value) for key in iterable)

    def __or__(self, other: Mapping[int, OtherValueT]) -> SafeIntegerDict[ValueT | OtherValueT]:
        """Merge mappings in average O(n + m) time, preferring other values.

        Args:
            other: Mapping with integer keys.

        Returns:
            A new dictionary containing both mappings.
        """
        if not isinstance(other, Mapping):  # pyright: ignore[reportUnnecessaryIsInstance]
            return NotImplemented
        result = SafeIntegerDict[ValueT | OtherValueT](self)
        result.update(other)
        return result

    def __ror__(self, other: Mapping[int, OtherValueT]) -> SafeIntegerDict[ValueT | OtherValueT]:
        """Merge mappings in average O(n + m) time, preferring self values.

        Args:
            other: Mapping with integer keys.

        Returns:
            A new dictionary containing both mappings.
        """
        if not isinstance(other, Mapping):  # pyright: ignore[reportUnnecessaryIsInstance]
            return NotImplemented
        result = SafeIntegerDict[ValueT | OtherValueT](other)
        result.update(self)
        return result

    def __ior__(self, other: Mapping[int, ValueT] | Iterable[tuple[int, ValueT]]) -> SafeIntegerDict[ValueT]:
        """Update this mapping in average O(m) time.

        Args:
            other: Mapping or key-value pairs; incoming values win.

        Returns:
            This dictionary.
        """
        self.update(other)
        return self

    @recursive_repr('{...}')
    def __repr__(self) -> str:
        """Return a representation with original keys in O(n) time.

        Returns:
            Dictionary notation; value formatting costs are additional.
        """
        return '{' + ', '.join(f'{key!r}: {value!r}' for key, value in self.items()) + '}'


class SafeIntegerSet(MutableSet[int]):
    """Set with collision-resistant storage for integer elements.

    Iteration and all set operations use the original integer elements.
    This is a MutableSet, not a set subclass. Hash-seed assumptions and
    large-integer costs are the same as for SafeIntegerDict. Binary set
    operators return SafeIntegerSet; the named methods also accept iterables.
    Converting to a built-in set restores ordinary integer hashing.

    Attributes:
        b: Random XOR mask; do not change it after construction.

    Space Complexity:
        O(n) for n bounded-size elements.

    Examples:
        >>> s = SafeIntegerSet([10, 20])
        >>> sorted(s.union([20, 30]))
        [10, 20, 30]
    """

    def __init__(self, values: Iterable[int] = ()) -> None:
        """Initialize from integer elements in average O(n) time.

        Args:
            values: Initial elements; duplicates are ignored.

        Returns:
            None.
        """
        self.b = random.getrandbits(30)
        self._data: set[int | bytes] = set()
        self.update(values)

    def __contains__(self, key: object) -> bool:
        """Test membership in average O(1) time.

        Args:
            key: Candidate element.

        Returns:
            Whether key is an integer stored in the set.
        """
        return isinstance(key, int) and _encode_integer(key, self.b) in self._data

    def __iter__(self) -> Iterator[int]:
        """Iterate over original elements in O(n) total time.

        Returns:
            An iterator over integer elements, in unspecified order.
        """
        mask = self.b
        return (_decode_integer(key, mask) for key in self._data)

    def __len__(self) -> int:
        """Return the element count in O(1) time.

        Returns:
            Number of distinct elements.
        """
        return len(self._data)

    def add(self, key: int) -> None:
        """Insert an element in average O(1) time.

        Args:
            key: Integer element.

        Returns:
            None, including when key already exists.
        """
        self._data.add(_encode_integer(key, self.b))

    def discard(self, key: object) -> None:
        """Remove an element if present in average O(1) time.

        Args:
            key: Candidate element.

        Returns:
            None, including when key is absent.
        """
        if isinstance(key, int):
            self._data.discard(_encode_integer(key, self.b))

    def remove(self, key: int) -> None:
        """Remove an element in average O(1) time.

        Args:
            key: Integer element.

        Returns:
            None.

        Raises:
            KeyError: If key is absent.
        """
        encoded = _encode_integer(key, self.b)
        try:
            self._data.remove(encoded)
        except KeyError:
            raise KeyError(key) from None

    def pop(self) -> int:
        """Remove an arbitrary element in average O(1) time.

        Returns:
            The removed integer element.

        Raises:
            KeyError: If the set is empty.
        """
        return _decode_integer(self._data.pop(), self.b)

    def clear(self) -> None:
        """Remove all elements in O(n) time.

        Returns:
            None.
        """
        self._data.clear()

    def copy(self) -> SafeIntegerSet:
        """Return a shallow copy in O(n) time.

        Returns:
            An independent set with the same elements.
        """
        result = SafeIntegerSet()
        result.b = self.b
        result._data = self._data.copy()
        return result

    def __copy__(self) -> SafeIntegerSet:
        """Implement copy.copy in O(n) time.

        Returns:
            An independent set containing the same elements.
        """
        return self.copy()

    def update(self, *others: Iterable[int]) -> None:
        """Insert elements from iterables in average O(m) time.

        Args:
            others: Iterables containing m elements in total.

        Returns:
            None.
        """
        for other in others:
            for key in other:
                self.add(key)

    def union(self, *others: Iterable[int]) -> SafeIntegerSet:
        """Return the union in average O(n + m) time.

        Args:
            others: Iterables containing m elements in total.

        Returns:
            A new set containing elements from any input.
        """
        result = self.copy()
        result.update(*others)
        return result

    def intersection(self, *others: Iterable[int]) -> SafeIntegerSet:
        """Return the intersection in average O(k * n + m) time.

        Args:
            others: k iterables containing m elements in total.

        Returns:
            A new set of elements present in every input; a copy if k is zero.
        """
        result = self.copy()
        result.intersection_update(*others)
        return result

    def intersection_update(self, *others: Iterable[int]) -> None:
        """Keep only common elements in average O(k * n + m) time.

        Args:
            others: k iterables containing m elements in total.

        Returns:
            None.
        """
        for other in others:
            candidates = other if isinstance(other, Set) else SafeIntegerSet(other)
            for key in list(self):
                if key not in candidates:
                    self.discard(key)

    def difference(self, *others: Iterable[int]) -> SafeIntegerSet:
        """Return the difference in average O(n + m) time.

        Args:
            others: Iterables containing m elements in total.

        Returns:
            A new set containing elements absent from all other inputs.
        """
        result = self.copy()
        result.difference_update(*others)
        return result

    def difference_update(self, *others: Iterable[int]) -> None:
        """Remove other elements in average O(m) time, or O(n) for self.

        Args:
            others: Iterables containing m elements in total.

        Returns:
            None.
        """
        for other in others:
            if other is self:
                self.clear()
            else:
                for key in other:
                    self.discard(key)

    def symmetric_difference(self, other: Iterable[int]) -> SafeIntegerSet:
        """Return the symmetric difference in average O(n + m) time.

        Args:
            other: Iterable of m elements.

        Returns:
            A new set containing elements present in exactly one input.
        """
        result = self.copy()
        result.symmetric_difference_update(other)
        return result

    def symmetric_difference_update(self, other: Iterable[int]) -> None:
        """Toggle elements in average O(m) time, or O(n) for self.

        Args:
            other: Iterable of m elements; duplicates are counted once.

        Returns:
            None.
        """
        if other is self:
            self.clear()
            return
        candidates = other if isinstance(other, Set) else SafeIntegerSet(other)
        for key in candidates:
            if key in self:
                self.discard(key)
            else:
                self.add(key)

    def issubset(self, other: Iterable[int]) -> bool:
        """Test containment in average O(n + m) time.

        Args:
            other: Iterable of m elements.

        Returns:
            Whether every element of this set occurs in other.
        """
        candidates = other if isinstance(other, Set) else SafeIntegerSet(other)
        return all(key in candidates for key in self)

    def issuperset(self, other: Iterable[int]) -> bool:
        """Test reverse containment in average O(m) time.

        Args:
            other: Iterable of m elements.

        Returns:
            Whether every element of other occurs in this set.
        """
        return all(key in self for key in other)

    def __repr__(self) -> str:
        """Return a representation with original elements in O(n) time.

        Returns:
            Set notation in unspecified element order.
        """
        return '{' + ', '.join(repr(key) for key in self) + '}' if self else 'set()'
