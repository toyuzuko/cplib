#!/usr/bin/env python3

from collections.abc import Sequence
from heapq import heapify, heappop, heappush


def minimum_non_adjacent_sums(values: Sequence[int]) -> list[int]:
    """
    Return minimum sums for every feasible non-adjacent selection size.

    Args:
        values: Integer weights on a path. Negative weights are allowed.

    Returns:
        A list whose entry ``k`` is the minimum sum of exactly ``k`` elements
        with no two selected indices consecutive. It contains
        ``(len(values) + 1) // 2 + 1`` entries and starts with zero.
        The input is not modified.

    Examples:
        >>> minimum_non_adjacent_sums([3, 1, 4, 1, 5])
        [0, 1, 2, 12]
        >>> minimum_non_adjacent_sums([-5, -8, -5])
        [0, -8, -10]
        >>> minimum_non_adjacent_sums([])
        [0]

    Time Complexity:
        O(n log(n + 1)), where ``n`` is ``len(values)``.

    Space Complexity:
        O(n)
    """
    costs = list(values)
    n = len(costs)
    left = [i - 1 for i in range(n)]
    right = [i + 1 for i in range(n)]
    if n:
        right[-1] = -1
    alive = [True] * n
    heap = [(value, i) for i, value in enumerate(costs)]
    heapify(heap)
    result = [0]
    for _ in range((n + 1) // 2):
        value, i = heappop(heap)
        while not alive[i]:
            value, i = heappop(heap)
        result.append(result[-1] + value)
        l, r = left[i], right[i]
        if l == -1 or r == -1:
            # An endpoint cannot be exchanged for two neighbors. Delete it
            # and its sole neighbor, rather than using a finite sentinel.
            alive[i] = False
            if l != -1:
                alive[l] = False
                ll = left[l]
                if ll != -1:
                    right[ll] = -1
            if r != -1:
                alive[r] = False
                rr = right[r]
                if rr != -1:
                    left[rr] = -1
        else:
            # Contract the three vertices. Choosing this vertex in a later
            # step replaces the previous choice by its two neighbors.
            costs[i] = costs[l] + costs[r] - value
            alive[l] = alive[r] = False
            ll, rr = left[l], right[r]
            left[i], right[i] = ll, rr
            if ll != -1:
                right[ll] = i
            if rr != -1:
                left[rr] = i
            heappush(heap, (costs[i], i))
    return result


def maximum_non_adjacent_sums(values: Sequence[int]) -> list[int]:
    """
    Return maximum sums for every feasible non-adjacent selection size.

    Args:
        values: Integer weights on a path. Negative weights are allowed.

    Returns:
        A list whose entry ``k`` is the maximum sum of exactly ``k`` elements
        with no two selected indices consecutive. It contains
        ``(len(values) + 1) // 2 + 1`` entries and starts with zero.
        The input is not modified.

    Examples:
        >>> maximum_non_adjacent_sums([3, 1, 4, 1, 5])
        [0, 5, 9, 12]
        >>> maximum_non_adjacent_sums([-5, -8, -5])
        [0, -5, -10]
        >>> maximum_non_adjacent_sums([])
        [0]

    Time Complexity:
        O(n log(n + 1)), where ``n`` is ``len(values)``.

    Space Complexity:
        O(n)
    """
    return [-value for value in minimum_non_adjacent_sums([-value for value in values])]
