#!/usr/bin/env python3

from typing import Generic
from collections.abc import Sequence, Callable
from cplib.tools.type import ValueT


class SparseTable(Generic[ValueT]):
    """
    Sparse Table for efficient range queries with idempotent operations.

    A data structure that preprocesses an array to answer range queries in O(1) time.
    Works with idempotent operations (op(x, x) = x) such as min, max, gcd, etc.

    Time Complexities:
        - construction: O(n log(n + 1))
        - prod (range query): O(1)

    Args:
        arr: Input array
        op: Associative, idempotent binary operation (e.g., min, max, gcd)

    Examples:
        >>> # Range minimum query
        >>> st = SparseTable([4, 2, 3, 7, 1, 5], min)
        >>> print(st.prod(1, 4))  # min of [2, 3, 7] = 2
        2

        >>> # Range maximum query
        >>> st = SparseTable([4, 2, 3, 7, 1, 5], max)
        >>> print(st.prod(2, 5))  # max of [3, 7, 1] = 7
        7

        >>> # Range GCD query
        >>> import math
        >>> st = SparseTable([12, 18, 24, 6], math.gcd)
        >>> print(st.prod(0, 4))  # gcd of [12, 18, 24, 6] = 6
        6

    Notes:
        The operation must be associative and idempotent: op(x, x) = x.
        Commutativity is not required. Callbacks must not mutate their inputs.
        Complexity bounds assume O(1) callbacks and fixed-size values.
        This property allows overlapping intervals in the query method.
        For non-idempotent operations, use segment trees instead.

    Space Complexity:
        O(n log(n + 1)) for the precomputed levels.
    """

    def __init__(self, arr: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT]) -> None:
        """Initialize sparse table with given array and operation.

        Time Complexity:
            O(n log n)

        Args:
            arr: Input sequence, copied during construction. Elements are not deep-copied.
            op: Associative, idempotent binary operation

        Returns:
            None.
        """
        self.n = len(arr)
        self.op = op
        self.log = self.n.bit_length()
        self.table = [list(arr)]
        prv = self.table[0]
        for i in range(1, self.log):
            nxt = [op(prv[j], prv[j + (1 << (i - 1))]) for j in range(self.n - (1 << i) + 1)]
            self.table.append(nxt)
            prv = nxt

    def prod(self, l: int, r: int) -> ValueT:
        """
        Compute the result of applying the operation to the elements in the range [l, r).

        Args:
            l (int): The left endpoint of the range.
            r (int): The right endpoint of the range.

        Returns:
            ValueT: The result of applying the operation to the elements in the range [l, r).

        Raises:
            AssertionError: If 0 <= l < r <= n does not hold.

        Time Complexity:
            O(1)
        """
        assert 0 <= l < r <= self.n
        b = r - l
        k = b.bit_length() - 1
        return self.op(self.table[k][l], self.table[k][r - (1 << k)])


class DisjointSparseTable(Generic[ValueT]):
    """
    Disjoint sparse table for associative range queries.

    A data structure that preprocesses an array to answer range queries in
    ``O(1)`` time using only associativity. Unlike :class:`SparseTable`, the
    operation does not need to be idempotent.

    Time Complexities:
        - construction: O(n log(n + 1))
        - prod (range query): O(1)

    Args:
        arr: Input array
        op: Associative binary operation

    Examples:
        >>> dst = DisjointSparseTable([1, 2, 3, 4], lambda x, y: x + y)
        >>> dst.prod(1, 4)
        9

        >>> dst = DisjointSparseTable(['a', 'b', 'c'], lambda x, y: x + y)
        >>> dst.prod(0, 3)
        'abc'

    Notes:
        The operation only needs to be associative. For idempotent operations
        such as ``min`` or ``max``, :class:`SparseTable` is usually simpler.
        Commutativity is not required. Callbacks must not mutate their inputs.
        Bounds assume O(1) callbacks and fixed-size values.

    Time Complexity:
        O(n log n) in the size of the processed input or stored data

    Space Complexity:
        O(n log(n + 1)) for the precomputed levels.
    """

    def __init__(self, arr: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT]) -> None:
        """Initialize disjoint sparse table with given array and operation.

        Time Complexity: O(n log n)

        Args:
            arr: Input sequence, copied during construction. Elements are not deep-copied.
            op: Associative binary operation

        Returns:
            None.
        """
        self.n = len(arr)
        self.op = op
        self.log = max(0, self.n - 1).bit_length() + 1
        self.table = [list(arr)]
        for k in range(1, self.log):
            row = list(arr)
            block = 1 << k
            half = block >> 1
            for mid in range(half, self.n, block):
                left = mid - 1
                start = mid - half
                row[left] = arr[left]
                for i in range(left - 1, start - 1, -1):
                    row[i] = op(arr[i], row[i + 1])
                if mid < self.n:
                    right = min(mid + half, self.n)
                    row[mid] = arr[mid]
                    for i in range(mid + 1, right):
                        row[i] = op(row[i - 1], arr[i])
            self.table.append(row)

    def prod(self, l: int, r: int) -> ValueT:
        """
        Compute the result of applying the operation to the elements in the range [l, r).

        Args:
            l (int): The left endpoint of the range.
            r (int): The right endpoint of the range.

        Returns:
            ValueT: The result of applying the operation to the elements in the range [l, r).

        Raises:
            AssertionError: If 0 <= l < r <= n does not hold.

        Time Complexity:
            O(1)
        """
        assert 0 <= l < r <= self.n
        b = r - l
        if b == 1:
            return self.table[0][l]
        k = (l ^ (r - 1)).bit_length()
        return self.op(self.table[k][l], self.table[k][r - 1])
