#!/usr/bin/env python3

"""Incremental linear algebra for nonnegative integer bit vectors over GF(2)."""

from collections.abc import Iterable


class XorBasis:
    """Maintain the span of nonnegative integers under XOR.

    Duplicate values and zero do not increase the rank. Integers have no fixed
    width. Negative values are rejected: Python's signed XOR has no finite
    highest pivot. The empty subset is included in all queries.

    Args:
        values: Initial bit vectors (optional).

    Examples:
        >>> basis = XorBasis([3, 5, 6])
        >>> len(basis)
        2
        >>> basis.add(6)
        False
        >>> 6 in basis, 1 in basis
        (True, False)
        >>> basis.max_xor(), basis.min_xor(7)
        (6, 1)

    Time Complexity:
        O(r) integer operations per insertion or query, where r is the rank.
        Construction takes O(k r) for k input values. Integer operations also
        depend on the operand bit lengths.

    Space Complexity:
        O(r) integers, each at most the maximum input bit length.
    """

    def __init__(self, values: Iterable[int] = ()) -> None:
        self._basis: list[int] = []
        for value in values:
            self.add(value)

    def __len__(self) -> int:
        """Return the rank (number of independent vectors) in O(1) time."""
        return len(self._basis)

    def add(self, value: int) -> bool:
        """Insert value; return True exactly when it increases the rank.

        Raises:
            ValueError: If value is negative.
        """
        if value < 0:
            raise ValueError('value must be nonnegative')
        for vector in self._basis:
            value = min(value, value ^ vector)
        if value == 0:
            return False
        # Descending highest pivots make greedy reduction valid.
        index = 0
        while index < len(self._basis) and self._basis[index] > value:
            index += 1
        self._basis.insert(index, value)
        return True

    def contains(self, value: int) -> bool:
        """Return whether value is in the span; negative values are rejected."""
        return self.min_xor(value) == 0

    def __contains__(self, value: int) -> bool:
        """Equivalent to contains(value)."""
        return self.contains(value)

    def min_xor(self, value: int = 0) -> int:
        """Minimize value XOR s over s in the span.

        Raises:
            ValueError: If value is negative.
        """
        if value < 0:
            raise ValueError('value must be nonnegative')
        for vector in self._basis:
            value = min(value, value ^ vector)
        return value

    def max_xor(self, value: int = 0) -> int:
        """Maximize value XOR s over s in the span.

        Raises:
            ValueError: If value is negative.
        """
        if value < 0:
            raise ValueError('value must be nonnegative')
        for vector in self._basis:
            value = max(value, value ^ vector)
        return value
