#!/usr/bin/env python3

"""Binary search utilities.

This module provides ordinary integer/real binary search helpers and a
parallel binary search scheduler for offline first-true queries.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from math import isfinite
from typing import TypeAlias
from cplib.tools.type import KeyT


_QueryRange: TypeAlias = tuple[int, int]

__all__ = [
    'ParallelBinarySearch',
    'binary_search',
    'float_binary_search',
    'bisect_left',
    'bisect_right',
]


def binary_search(ng: int, ok: int, check: Callable[[int], bool]) -> int:
    """Find the boundary of a monotone integer predicate.

    Args:
        ng: Boundary known to be false.
        ok: Boundary known to be true.
        check: Monotone predicate. ``check(ok)`` must be true and
            ``check(ng)`` must be false.

    Returns:
        The closest true boundary to ``ng``. For increasing predicates this is
        the minimum true index; for decreasing searches, pass ``ng > ok``.

    Time Complexity:
        ``O(log(abs(ok - ng)))`` predicate evaluations.

    Space Complexity:
        ``O(1)``

    Examples:
        >>> is_valid = lambda x: x >= 10
        >>> # The smallest index where `is_valid` is true is 10.
        >>> binary_search(0, 20, is_valid)
        10
    """
    while abs(ok - ng) > 1:
        mid = (ok + ng) // 2
        if check(mid):
            ok = mid
        else:
            ng = mid
    return ok


def float_binary_search(ng: float, ok: float, check: Callable[[float], bool], iterations: int = 80) -> float:
    """Find an approximate boundary of a monotone real predicate.

    Args:
        ng: Finite boundary known to be false.
        ok: Finite boundary known to be true.
        check: Monotone predicate.
        iterations: Non-negative maximum number of bisection steps.

    Returns:
        Approximate true boundary after at most ``iterations`` bisection
        steps. Stops early when the midpoint rounds to either endpoint.

    Raises:
        ValueError: If an endpoint is not finite or ``iterations`` is negative.

    Time Complexity:
        ``O(iterations)`` predicate evaluations.

    Space Complexity:
        ``O(1)``

    Examples:
        >>> is_valid = lambda x: x >= 10.5
        >>> # After enough iterations, the result is close to the smallest index where `is_valid` is true.
        >>> float_binary_search(0.0, 20.0, is_valid)
        10.5
    """
    if not isfinite(ng) or not isfinite(ok):
        raise ValueError('endpoints must be finite')
    if iterations < 0:
        raise ValueError('iterations must be non-negative')
    for _ in range(iterations):
        mid = ng + (ok - ng) / 2 if (ng < 0) == (ok < 0) else (ok + ng) / 2
        if mid == ng or mid == ok:
            break
        if check(mid):
            ok = mid
        else:
            ng = mid
    return ok


def bisect_left(arr: Sequence[KeyT], x: KeyT) -> int:
    """Return the first index ``i`` such that ``arr[i] >= x``.

    Args:
        arr: Sorted sequence.
        x: Target value.

    Returns:
        Insertion position before equal elements.

    Time Complexity:
        ``O(log n)``

    Space Complexity:
        ``O(1)``

    Examples:
        >>> arr = [1, 3, 3, 5, 7]
        >>> # The first index where `3` can be inserted without violating the order is index `1`, before the existing `3`s.
        >>> bisect_left(arr, 3)
        1
    """
    lo = 0
    hi = len(arr)
    while lo < hi:
        mid = (lo + hi) >> 1
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def bisect_right(arr: Sequence[KeyT], x: KeyT) -> int:
    """Return the first index ``i`` such that ``arr[i] > x``.

    Args:
        arr: Sorted sequence.
        x: Target value.

    Returns:
        Insertion position after equal elements.

    Time Complexity:
        ``O(log n)``

    Space Complexity:
        ``O(1)``

    Examples:
        >>> arr = [1, 3, 3, 5, 7]
        >>> # The first index where `3` can be inserted without violating the order is index `3`, after the existing `3`s.
        >>> bisect_right(arr, 3)
        3
    """
    lo = 0
    hi = len(arr)
    while lo < hi:
        mid = (lo + hi) >> 1
        if x < arr[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


class ParallelBinarySearch:
    """Schedule multiple first-true searches on a growing prefix.

    The structure manages offline binary searches over prefix lengths:

    - prefix length ``0`` means no updates have been applied yet
    - prefix length ``k`` means ``apply(0)`` through ``apply(k - 1)`` have been
      executed after ``reset()``
    - the returned answer is the minimum prefix length where ``check(i)`` is
      true for query ``i``
    - if a query never becomes true within ``0..steps``, the answer is
      ``steps + 1``

    Queries are stored as ``(ng, ok)`` pairs. They follow the usual first-true
    convention:

    - ``ng`` is a known false boundary
    - ``ok`` is a known true boundary, or the sentinel ``steps + 1`` meaning
      "not found yet"

    Attributes:
        steps: Number of updates in the underlying prefix.
        _queries: Stored ``(ng, ok)`` boundary pairs.

    Space Complexity:
        ``O(q)``

    Examples:
        Find the first prefix length at which each threshold is reached.

        ``values`` are applied from left to right.  For each target, the query
        asks for the minimum prefix length whose prefix sum is at least that
        target.
        >>> values = [3, 1, 4, 1, 5]
        >>> targets = [0, 4, 8, 20]
        >>>
        >>> pbs = ParallelBinarySearch(len(values))
        >>> for _ in targets:
        ...     _ = pbs.add_query()
        ...
        >>> state = {'total': 0}
        >>>
        >>> def reset() -> None:
        ...     state['total'] = 0
        ...
        >>> def apply(i: int) -> None:
        ...     state['total'] += values[i]
        ...
        >>> def check(i: int) -> bool:
        ...     return state['total'] >= targets[i]
        ...
        >>> pbs.run(reset, apply, check)
        [0, 2, 3, 6]
    """

    def __init__(self, steps: int) -> None:
        """Initialize a parallel binary search scheduler.

        Args:
            steps: Number of updates in the prefix.

        Returns:
            None.

        Raises:
            ValueError: If ``steps`` is negative.

        Time Complexity:
            O(1)
        """
        if steps < 0:
            raise ValueError('steps must be non-negative')
        self.steps = steps
        self._queries: list[_QueryRange] = []

    def __len__(self) -> int:
        """Return the number of stored queries."""
        return len(self._queries)

    @property
    def queries(self) -> list[_QueryRange]:
        """
        Return a shallow copy of stored ``(ng, ok)`` boundary pairs.

        Returns:
            Stored query boundaries.

        Time Complexity:
            ``O(q)``
        """
        return self._queries[:]

    def add_query(self, ng: int = -1, ok: int | None = None) -> int:
        """Store one first-true query.

        Args:
            ng: Known-false boundary.
            ok: Known-true boundary, or ``None`` to use ``steps + 1``.

        Returns:
            Index assigned to the inserted query.

        Raises:
            ValueError: If boundaries do not satisfy
                ``-1 <= ng < ok <= steps + 1``.

        Time Complexity:
            ``O(1)`` amortized.
        """
        if ok is None:
            ok = self.steps + 1
        if not (-1 <= ng < ok <= self.steps + 1):
            raise ValueError('query boundaries must satisfy -1 <= ng < ok <= steps + 1')
        self._queries.append((ng, ok))
        return len(self._queries) - 1

    def run(self, reset: Callable[[], None], apply: Callable[[int], None], check: Callable[[int], bool]) -> list[int]:
        """Resolve all stored queries with parallel binary search.

        Args:
            reset: Reset the underlying structure to prefix length ``0``.
            apply: Apply update ``i`` and advance the prefix length by one.
            check: Evaluate whether query ``i`` is true at the current prefix.

        Returns:
            The minimum prefix length for each query, or ``steps + 1`` when the
            predicate never becomes true.

        Time Complexity:
            ``O((steps + q) log(steps + 2))`` calls to ``apply`` and ``check``,
            where ``q`` is the number of stored queries.
            Sorting the occupied buckets adds
            ``O(q log(q + 1) log(steps + 2))`` time in the worst case.

        Space Complexity:
            ``O(q)``
        """
        q = len(self._queries)
        if q == 0:
            return []

        ng: list[int] = [pair[0] for pair in self._queries]
        ok: list[int] = [pair[1] for pair in self._queries]

        active: list[int] = list(range(q))
        while active:
            buckets: dict[int, list[int]] = {}
            for idx in active:
                if ng[idx] + 1 >= ok[idx]:
                    continue
                mid = (ng[idx] + ok[idx]) // 2
                if mid not in buckets:
                    buckets[mid] = []
                buckets[mid].append(idx)

            if not buckets:
                break

            reset()
            current = 0
            for mid in sorted(buckets):
                while current < mid:
                    apply(current)
                    current += 1
                for idx in buckets[mid]:
                    if check(idx):
                        ok[idx] = mid
                    else:
                        ng[idx] = mid

            active = [idx for idx in active if ng[idx] + 1 < ok[idx]]

        return ok
