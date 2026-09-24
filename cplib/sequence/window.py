#!/usr/bin/env python3

from collections import Counter, defaultdict
from collections.abc import Hashable, Iterable, Sequence
from typing import TypeVar


HashableT = TypeVar('HashableT', bound=Hashable)


def count_subarrays_with_sum(arr: Sequence[int], target: int) -> int:
    """
    Count non-empty contiguous subarrays whose sum is exactly ``target``.

    Args:
        arr: Integer sequence.
        target: Target subarray sum.

    Returns:
        Number of contiguous subarrays with sum equal to ``target``.

    Time Complexity:
        O(n), where ``n`` is ``len(arr)``.

    Space Complexity:
        O(n)
    """
    counts: defaultdict[int, int] = defaultdict(int)
    counts[0] = 1
    prefix = 0
    result = 0
    for value in arr:
        prefix += value
        result += counts[prefix - target]
        counts[prefix] += 1
    return result


def count_subarrays_with_sum_at_most_nonnegative(arr: Sequence[int], upper: int) -> int:
    """
    Count non-empty contiguous subarrays whose sum is at most ``upper``.

    Args:
        arr: Non-negative integer sequence.
        upper: Inclusive upper bound for subarray sums.

    Returns:
        Number of contiguous subarrays with sum at most ``upper``.

    Raises:
        ValueError: If ``arr`` contains a negative value.

    Time Complexity:
        O(n), where ``n`` is ``len(arr)``.

    Space Complexity:
        O(1)
    """
    if upper < 0:
        if any(value < 0 for value in arr):
            raise ValueError('all values must be non-negative')
        return 0

    left = 0
    total = 0
    result = 0
    for right, value in enumerate(arr):
        if value < 0:
            raise ValueError('all values must be non-negative')
        total += value
        while total > upper:
            total -= arr[left]
            left += 1
        result += right - left + 1
    return result


def minimum_subarray_length_with_sum_at_least_nonnegative(arr: Sequence[int], lower: int) -> int:
    """
    Return the shortest length of a subarray whose sum is at least ``lower``.

    Args:
        arr: Non-negative integer sequence.
        lower: Inclusive lower bound for subarray sums.

    Returns:
        Minimum subarray length, or ``0`` if no subarray has sum at least
        ``lower``. The empty subarray is allowed, so ``lower <= 0`` returns 0.

    Raises:
        ValueError: If ``arr`` contains a negative value.

    Time Complexity:
        O(n), where ``n`` is ``len(arr)``.

    Space Complexity:
        O(1)
    """
    if lower <= 0:
        if any(value < 0 for value in arr):
            raise ValueError('all values must be non-negative')
        return 0

    left = 0
    total = 0
    best = len(arr) + 1
    for right, value in enumerate(arr):
        if value < 0:
            raise ValueError('all values must be non-negative')
        total += value
        while total >= lower:
            length = right - left + 1
            if length < best:
                best = length
            total -= arr[left]
            left += 1
    return 0 if best == len(arr) + 1 else best


def minimum_window_covering_multiset(arr: Sequence[HashableT], required: Iterable[HashableT]) -> int:
    """
    Return the shortest contiguous window covering a required multiset.

    Args:
        arr: Sequence to search.
        required: Required values with multiplicities.

    Returns:
        Minimum window length, or ``0`` if no window covers ``required``.
        If ``required`` is empty, returns ``0``.

    Time Complexity:
        O(n + k), where ``n`` is ``len(arr)`` and ``k`` is the number of
        required elements including multiplicities.

    Space Complexity:
        O(d), where ``d`` is the number of distinct required values.
    """
    need = Counter(required)
    if not need:
        return 0

    have: defaultdict[HashableT, int] = defaultdict(int)
    satisfied = 0
    distinct_required = len(need)
    left = 0
    best = len(arr) + 1

    for right, value in enumerate(arr):
        if value in need:
            have[value] += 1
            if have[value] == need[value]:
                satisfied += 1

        while satisfied == distinct_required:
            length = right - left + 1
            if length < best:
                best = length
            removed = arr[left]
            if removed in need:
                if have[removed] == need[removed]:
                    satisfied -= 1
                have[removed] -= 1
            left += 1

    return 0 if best == len(arr) + 1 else best
