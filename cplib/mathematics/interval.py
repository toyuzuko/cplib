#!/usr/bin/env python3

from collections.abc import Iterator
from heapq import heapify, heapreplace


def range_mod(l: int, r: int, mod: int) -> Iterator[tuple[int, int, int]]:
    """
    Generate normalized modulo subranges for the integer range ``[l, r)``.

    This function divides ``[l, r)`` by residue modulo ``mod`` and yields
    triples describing contiguous residue ranges and how many full periods they
    represent.

    Args:
        l: Left boundary of the range, inclusive.
        r: Right boundary of the range, exclusive.
        mod: Positive modulus used to normalize the range.

    Yields:
        Tuples ``(left, right, count)``, where ``[left, right)`` is a residue
        nonempty range and count is its multiplicity. Ranges may overlap;
        add their counts to recover residue frequencies. Empty input yields
        no triples.

    Raises:
        AssertionError: If l > r or mod <= 0, on iterator consumption.

    Examples:
        >>> list(range_mod(2, 11, 3))
        [(2, 3, 1), (0, 3, 2), (0, 2, 1)]

    Time Complexity:
        O(1)

    Space Complexity:
        O(1) auxiliary space
    """
    assert l <= r and 0 < mod
    if l == r:
        return
    lq, _ = divmod(l, mod)
    l -= lq * mod
    r -= lq * mod
    if r < mod:
        yield l, r, 1
    else:
        yield l, mod, 1
        if (r - mod) // mod > 0:
            yield 0, mod, (r - mod) // mod
        if (r - mod) % mod > 0:
            yield 0, (r - mod) % mod, 1


def interval_union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Compute the union of a list of half-open intervals.

    Given intervals ``[a_1, b_1), [a_2, b_2), ..., [a_n, b_n)``, this function
    returns their union as a disjoint sorted list of half-open intervals.

    Args:
        intervals: List of half-open intervals ``(l, r)``.

    Returns:
        Sorted nonempty intervals representing the union. Empty intervals
        are ignored and touching intervals are merged. The input is unchanged.

    Raises:
        ValueError: If some interval does not satisfy ``l <= r``.

    Time Complexity:
        ``O(n log n)``, where ``n = len(intervals)``.

    Space Complexity:
        ``O(n)``

    Examples:
        >>> interval_union([(1, 4), (2, 5), (7, 9)])
        [(1, 5), (7, 9)]
        >>> interval_union([(1, 3), (3, 5)])
        [(1, 5)]
    """
    for left, right in intervals:
        if left > right:
            raise ValueError('each interval must satisfy l <= r')
    result: list[tuple[int, int]] = []
    for left, right in sorted(intervals):
        if left == right:
            continue
        if result and left <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], right))
        else:
            result.append((left, right))
    return result


def interval_intersection(interval_lists: list[list[tuple[int, int]]]) -> list[tuple[int, int]]:
    """
    Compute the common intersection of sorted disjoint interval lists.

    Given interval lists ``S_1, S_2, ..., S_k``, where each ``S_i`` is a sorted
    disjoint list of half-open intervals, this function returns the common
    intersection ``S_1 ∩ S_2 ∩ ... ∩ S_k`` as a sorted disjoint list.

    Args:
        interval_lists: Sorted lists with disjoint interiors. Touching
            intervals are allowed (previous_right <= next_left). Empty
            intervals are allowed but contribute no points.

    Returns:
        Sorted disjoint intervals representing the common intersection of all
        interval lists. Adjacent output intervals are merged; zero input
        lists or any empty input list produces an empty result.

    Raises:
        ValueError: If some interval does not satisfy ``l <= r``.
        ValueError: If some interval list is not sorted and disjoint.

    Time Complexity:
        ``O(T log k)``, where ``T`` is the total number of intervals and ``k``
        is the number of interval lists.

    Space Complexity:
        ``O(k + a)``, where ``a`` is the number of output intervals.
    """
    if len(interval_lists) == 0:
        return []
    for intervals in interval_lists:
        previous_right = -1 << 60
        for index, (left, right) in enumerate(intervals):
            if left > right:
                raise ValueError("each interval must satisfy l <= r")
            if index > 0 and previous_right > left:
                raise ValueError("each interval list must be sorted and disjoint")
            previous_right = right

    if any(len(intervals) == 0 for intervals in interval_lists):
        return []

    positions = [0] * len(interval_lists)
    right_heap = [
        (intervals[0][1], list_index)
        for list_index, intervals in enumerate(interval_lists)
    ]
    heapify(right_heap)
    current_max_left = max(intervals[0][0] for intervals in interval_lists)
    intersection_intervals: list[tuple[int, int]] = []

    while True:
        current_min_right, list_index = right_heap[0]
        if current_max_left < current_min_right:
            if intersection_intervals and intersection_intervals[-1][1] == current_max_left:
                intersection_intervals[-1] = (intersection_intervals[-1][0], current_min_right)
            else:
                intersection_intervals.append((current_max_left, current_min_right))

        positions[list_index] += 1
        if positions[list_index] == len(interval_lists[list_index]):
            return intersection_intervals

        next_left, next_right = interval_lists[list_index][positions[list_index]]
        current_max_left = max(current_max_left, next_left)
        heapreplace(right_heap, (next_right, list_index))
