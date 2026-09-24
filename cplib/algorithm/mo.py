#!/usr/bin/env python3

"""Mo-style offline range query ordering.

This module provides three practical variants for contest code:

- ``Mo``: standard block ordering with add/remove on both ends
- ``HilbertMo``: Hilbert-order sorting for better locality
- ``RollbackMo``: rollback-based ordering for data structures without deletions
"""

from __future__ import annotations

from collections.abc import Callable
from math import isqrt
from typing import Generic, TypeVar, cast

from cplib.tools.type import ValueT

SnapshotT = TypeVar('SnapshotT')


def hilbert_order(x: int, y: int, power: int) -> int:
    """Return the Hilbert-curve index of a point in a square grid.

    Args:
        x: First coordinate, with ``0 <= x < 2**power``.
        y: Second coordinate, with ``0 <= y < 2**power``.
        power: Non-negative number of coordinate bits. Use the same power
            for all points whose indices will be compared.

    Returns:
        Index in ``[0, 2**(2 * power))``. For ``power == 0``, the only
        valid point is ``(0, 0)`` and its index is zero.

    Raises:
        ValueError: If power is negative or either coordinate is out of range.

    Time Complexity:
        O(power) integer operations.

    Space Complexity:
        O(1) auxiliary integers.

    Examples:
        >>> [hilbert_order(x, y, 1) for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]]
        [0, 1, 2, 3]
    """
    if power < 0:
        raise ValueError('power must be non-negative')
    if not (0 <= x < 1 << power and 0 <= y < 1 << power):
        raise ValueError('coordinates must lie in [0, 2**power)')
    result = 0
    direction = 1
    rotate = 0
    rotate_delta = (3, 0, 0, 1)
    for level in range(power - 1, -1, -1):
        half = 1 << level
        if x < half:
            segment = 0 if y < half else 3
        else:
            segment = 1 if y < half else 2
        segment = (segment + rotate) & 3
        size = 1 << (2 * level)
        result += direction * segment * size
        if segment == 0 or segment == 3:
            result += direction * (size - 1)
            direction = -direction
        rotate = (rotate + rotate_delta[segment]) & 3
        x &= half - 1
        y &= half - 1
    return result


class Mo(Generic[ValueT]):
    """Standard Mo's algorithm scheduler for half-open range queries.

    This class stores offline queries on intervals ``[l, r)`` and reorders them
    so adjacent queries differ by only a small number of pointer moves. It is
    suitable for data structures that can:

    - add one element on the left
    - add one element on the right
    - remove one element from the left
    - remove one element from the right

    Attributes:
        n: Length of the underlying array.
        block_size: Optional block size for the left endpoint.
        _queries: Stored half-open query intervals.

    Space Complexity:
        - ``O(q)``

    Examples:
        >>> arr = [1, 2, 3, 4]
        >>> mo = Mo[int](len(arr))
        >>> mo.add_query(1, 3)
        0
        >>> total = 0
        >>> ans = mo.run(
        ...     add_left=lambda i: None,
        ...     add_right=lambda i: None,
        ...     remove_left=lambda i: None,
        ...     remove_right=lambda i: None,
        ...     answer=lambda _: 0,
        ... )
        >>> ans
        [0]
    """

    def __init__(self, n: int, block_size: int | None = None) -> None:
        """Initialize an empty range-query scheduler.

        Args:
            n: Non-negative length of the underlying array.
            block_size: Positive left-endpoint block size. If None, choose it
                from n and the number of queries when computing the order.

        Returns:
            None.

        Raises:
            ValueError: If n is negative or block_size is not positive.

        Time Complexity:
            O(1)
        """
        if n < 0:
            raise ValueError("n must be non-negative")
        if block_size is not None and block_size <= 0:
            raise ValueError("block_size must be positive")
        self.n = n
        self.block_size = block_size
        self._queries: list[tuple[int, int]] = []

    def __len__(self) -> int:
        """Return the number of stored queries.

        Returns:
            Number of stored queries.

        Time Complexity:
            - ``O(1)``
        """

        return len(self._queries)

    @property
    def queries(self) -> list[tuple[int, int]]:
        """Return the stored queries as ``(l, r)`` pairs.

        Returns:
            Copy of the internal query list.

        Time Complexity:
            - ``O(q)``
        """

        return self._queries[:]

    def add_query(self, l: int, r: int) -> int:
        """Store a half-open query interval ``[l, r)``.

        Args:
            l: Left endpoint.
            r: Right endpoint.

        Returns:
            Index assigned to the inserted query.

        Raises:
            ValueError: If the interval is outside ``[0, n]`` or ``l > r``.

        Time Complexity:
            - ``O(1)``
        """

        if not 0 <= l <= r <= self.n:
            raise ValueError("query must satisfy 0 <= l <= r <= n")
        self._queries.append((l, r))
        return len(self._queries) - 1

    def _resolved_block_size(self) -> int:
        if self.block_size is not None:
            return self.block_size
        q = max(1, len(self._queries))
        return max(1, self.n // max(1, isqrt(q)))

    def order(self) -> list[int]:
        """Return query indices in Mo order.

        Returns:
            Query indices sorted for standard Mo processing.

        Time Complexity:
            - ``O(q log q)``
        """

        block = self._resolved_block_size()
        order = list(range(len(self._queries)))
        order.sort(
            key=lambda i: (
                self._queries[i][0] // block,
                self._queries[i][1]
                if ((self._queries[i][0] // block) & 1) == 0
                else -self._queries[i][1],
            )
        )
        return order

    def run(self,
        add_left: Callable[[int], None],
        add_right: Callable[[int], None],
        remove_left: Callable[[int], None],
        remove_right: Callable[[int], None],
        answer: Callable[[int], ValueT],
    ) -> list[ValueT]:
        """Process all queries in Mo order.

        The callbacks are invoked with array indices. At the moment
        ``answer(query_index)`` is called, the active segment is exactly the
        corresponding query interval.

        The callback state must represent an empty interval on entry. On
        return it represents the final processed interval; reset that state
        before calling this method again.

        Args:
            add_left: Add index ``i`` when extending the left border to ``i``.
            add_right: Add index ``i`` when extending the right border to
                include ``i``.
            remove_left: Remove index ``i`` when moving the left border past it.
            remove_right: Remove index ``i`` when shrinking the right border
                past it.
            answer: Produce the result for the current query.

        Returns:
            Results in the original query order.

        Time Complexity:
            - Depends on callback costs and query order; typically
              ``O((n + q) sqrt(n))`` callback invocations

        Examples:
            >>> arr = [1, 2, 3]
            >>> freq = 0
            >>> mo = Mo[int](3)
            >>> mo.add_query(0, 2)
            0
            >>> ans = mo.run(
            ...     add_left=lambda i: None,
            ...     add_right=lambda i: None,
            ...     remove_left=lambda i: None,
            ...     remove_right=lambda i: None,
            ...     answer=lambda _: 7,
            ... )
            >>> ans
            [7]
        """

        result: list[ValueT | None] = [None] * len(self._queries)
        left = 0
        right = 0
        for query_index in self.order():
            ql, qr = self._queries[query_index]
            while left > ql:
                left -= 1
                add_left(left)
            while right < qr:
                add_right(right)
                right += 1
            while left < ql:
                remove_left(left)
                left += 1
            while right > qr:
                right -= 1
                remove_right(right)
            result[query_index] = answer(query_index)
        return [cast(ValueT, value) for value in result]


class HilbertMo(Mo[ValueT]):
    """Mo's algorithm variant that sorts queries by Hilbert order.

    Hilbert ordering often improves constant factors when the active data
    structure is sensitive to cache locality.
    Time complexity is typically similar to standard Mo, but the exact number of
    pointer moves may differ.

    Attributes:
        n: Length of the underlying array.
        block_size: Fixed block size placeholder inherited from :class:`Mo`.
        _queries: Stored half-open query intervals.

    Space Complexity:
        - ``O(q)``

    Examples:
        >>> mo = HilbertMo[int](5)
        >>> mo.add_query(1, 4)
        0
        >>> mo.add_query(0, 3)
        1
        >>> mo.add_query(2, 5)
        2
        >>> # The order of query indices may differ from insertion order due to Hilbert sorting.
        >>> mo.order()
        [1, 2, 0]
    """

    def __init__(self, n: int) -> None:
        """Initialize an empty scheduler using Hilbert order.

        Args:
            n: Non-negative length of the underlying array.

        Returns:
            None.

        Raises:
            ValueError: If n is negative.

        Time Complexity:
            O(1)
        """
        super().__init__(n=n, block_size=1)

    def order(self) -> list[int]:
        """Return query indices in Hilbert order.

        Returns:
            Query indices sorted by Hilbert curve order of ``(l, r)``.

        Time Complexity:
            - ``O(q log q)``
        """

        power = max(1, self.n.bit_length())
        order = list(range(len(self._queries)))
        order.sort(
            key=lambda i: hilbert_order(
                self._queries[i][0],
                self._queries[i][1],
                power,
            )
        )
        return order


class RollbackMo(Generic[ValueT, SnapshotT]):
    """Rollback Mo's algorithm for data structures without deletions.

    This variant is useful when the active structure supports:

    - adding an index to the current set
    - taking a snapshot
    - rolling back to a previous snapshot

    Queries are grouped by the block of their left endpoint. Intervals fully
    contained in one block are handled independently; the others are processed
    with a growing right border and temporary additions on the left.

    Attributes:
        n: Length of the underlying array.
        block_size: Optional left-block size.
        _queries: Stored half-open query intervals.

    Space Complexity:
        - ``O(q)`` plus the underlying rollback structure

    Examples:
        >>> a = [3, 1, 4, 1, 5, 9, 2]
        >>> mo = RollbackMo[int, int](len(a))
        >>> mo.add_query(0, 3)
        0
        >>> mo.add_query(2, 6)
        1
        >>> mo.add_query(4, 7)
        2
        >>> class RangeMaximum:
        ...     def __init__(self) -> None:
        ...         self.value = 0
        ...         self.history = []
        ...     def add(self, i: int) -> None:
        ...         self.history.append(self.value)
        ...         self.value = max(self.value, a[i])
        ...     def snapshot(self) -> int:
        ...         return len(self.history)
        ...     def rollback(self, snap: int) -> None:
        ...         while len(self.history) > snap:
        ...             self.value = self.history.pop()
        ...     def answer(self, _: int) -> int:
        ...         return self.value
        >>> ds = RangeMaximum()
        >>> mo.run(ds.add, ds.snapshot, ds.rollback, ds.answer)
        [4, 9, 9]
    """

    def __init__(self, n: int, block_size: int | None = None) -> None:
        """
        Initialize an empty scheduler for rollback-based range queries.

        Args:
            n: Length of the underlying array.
            block_size: Optional block size for the left endpoint.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative or if ``block_size`` is non-positive.

        Time Complexity:
            O(1)
        """

        if n < 0:
            raise ValueError("n must be non-negative")
        if block_size is not None and block_size <= 0:
            raise ValueError("block_size must be positive")
        self.n = n
        self.block_size = block_size
        self._queries: list[tuple[int, int]] = []

    def __len__(self) -> int:
        """Return the number of stored queries.

        Returns:
            Number of stored queries.

        Time Complexity:
            - ``O(1)``
        """

        return len(self._queries)

    @property
    def queries(self) -> list[tuple[int, int]]:
        """Return the stored queries as ``(l, r)`` pairs.

        Returns:
            Copy of the stored queries.

        Time Complexity:
            - ``O(q)``
        """

        return self._queries[:]

    def add_query(self, l: int, r: int) -> int:
        """Store a half-open query interval ``[l, r)``.

        Args:
            l: Left endpoint.
            r: Right endpoint.

        Returns:
            Index assigned to the inserted query.

        Raises:
            ValueError: If the interval is outside ``[0, n]`` or ``l > r``.

        Time Complexity:
            - ``O(1)``
        """

        if not 0 <= l <= r <= self.n:
            raise ValueError("query must satisfy 0 <= l <= r <= n")
        self._queries.append((l, r))
        return len(self._queries) - 1

    def _resolved_block_size(self) -> int:
        if self.block_size is not None:
            return self.block_size
        return max(1, isqrt(max(1, self.n)))

    def order(self) -> list[int]:
        """Return query indices grouped for rollback Mo processing.

        Returns:
            Query indices sorted by left block and then by right endpoint.

        Time Complexity:
            - ``O(q log q)``
        """

        block = self._resolved_block_size()
        order = list(range(len(self._queries)))
        order.sort(key=lambda i: (self._queries[i][0] // block, self._queries[i][1]))
        return order

    def run(self, add: Callable[[int], None], snapshot: Callable[[], SnapshotT], rollback: Callable[[SnapshotT], None], answer: Callable[[int], ValueT]) -> list[ValueT]:
        """Process all queries using rollback Mo.

        The callback ``add(i)`` is called when index ``i`` enters the active
        range. The implementation never asks the data structure to delete an
        element directly; temporary additions are undone through
        ``rollback(snapshot())``.

        The callback state must represent an empty set on entry and is
        restored on normal return. Answers must be independent of the order
        in which active indices were added.

        Args:
            add: Add one index to the active set.
            snapshot: Capture the current rollback state.
            rollback: Restore a previous snapshot.
            answer: Produce the result for the current query.

        Returns:
            Results in the original query order.

        Time Complexity:
            - Typically ``O((n + q) sqrt(n))`` additions and rollbacks

        Space Complexity:
            - ``O(q + n / B + 1)``, where ``B`` is the resolved block size,
              excluding the callback structure and its rollback history.

        Examples:
            >>> a = [3, 1, 4, 1, 5, 9, 2]
            >>> mo = RollbackMo[int, int](len(a))
            >>> mo.add_query(0, 3)
            0
            >>> mo.add_query(2, 6)
            1
            >>> mo.add_query(4, 7)
            2
            >>> class RangeMaximum:
            ...     def __init__(self) -> None:
            ...         self.value = 0
            ...         self.history = []
            ...     def add(self, i: int) -> None:
            ...         self.history.append(self.value)
            ...         self.value = max(self.value, a[i])
            ...     def snapshot(self) -> int:
            ...         return len(self.history)
            ...     def rollback(self, snap: int) -> None:
            ...         while len(self.history) > snap:
            ...             self.value = self.history.pop()
            ...     def answer(self, _: int) -> int:
            ...         return self.value
            >>> ds = RangeMaximum()
            >>> mo.run(ds.add, ds.snapshot, ds.rollback, ds.answer)
            [4, 9, 9]
        """

        query_count = len(self._queries)
        result: list[ValueT | None] = [None] * query_count
        if query_count == 0:
            return []

        block = self._resolved_block_size()
        bucket_count = (self.n + block - 1) // block + 1
        buckets: list[list[int]] = [[] for _ in range(bucket_count)]
        for query_index, (l, _) in enumerate(self._queries):
            buckets[l // block].append(query_index)

        for block_index, bucket in enumerate(buckets):
            if not bucket:
                continue
            bucket_start = block_index * block
            bucket_end = min(self.n, bucket_start + block)
            empty = snapshot()

            short_queries: list[int] = []
            long_queries: list[int] = []
            for query_index in bucket:
                _, r = self._queries[query_index]
                if r <= bucket_end:
                    short_queries.append(query_index)
                else:
                    long_queries.append(query_index)

            short_queries.sort(key=lambda i: self._queries[i][1])
            for query_index in short_queries:
                local = snapshot()
                l, r = self._queries[query_index]
                for pos in range(l, r):
                    add(pos)
                result[query_index] = answer(query_index)
                rollback(local)

            if not long_queries:
                rollback(empty)
                continue

            rollback(empty)
            long_queries.sort(key=lambda i: self._queries[i][1])
            right = bucket_end
            for query_index in long_queries:
                l, r = self._queries[query_index]
                while right < r:
                    add(right)
                    right += 1
                local = snapshot()
                for pos in range(bucket_end - 1, l - 1, -1):
                    add(pos)
                result[query_index] = answer(query_index)
                rollback(local)
            rollback(empty)

        return [cast(ValueT, value) for value in result]


__all__ = ['Mo', 'HilbertMo', 'RollbackMo', 'hilbert_order']
