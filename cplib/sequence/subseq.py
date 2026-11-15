#!/usr/bin/env python3

from bisect import bisect_left
from collections.abc import Sequence
from heapq import heapify, heappop, heappush


def longest_increasing_subsequence(arr: list[int], return_idx: bool = False) -> list[int]:
    """Return one longest increasing subsequence.

    The implementation uses the standard patience-sorting style dynamic
    programming with binary search and reconstructs one valid LIS.

    Args:
        arr: Input array.
        return_idx: If true, return indices instead of values.

    Returns:
        One longest increasing subsequence. When ``return_idx=True``, returns
        the indices of the chosen subsequence in increasing order.

    Time Complexity:
        ``O(n log n)``

    Space Complexity:
        ``O(n)``

    Examples:
        >>> longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18])
        [2, 3, 7, 18]
        >>> longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18], return_idx=True)
        [2, 4, 5, 7]
    """
    n = len(arr)
    if n == 0:
        return []
    dp1: list[int] = []
    dp2 = [-1] * n
    for i, a in enumerate(arr):
        idx = bisect_left(dp1, a)
        if idx == len(dp1):
            dp1.append(a)
        else:
            dp1[idx] = a
        dp2[i] = idx
    idx = max(dp2)
    lis = [0] * (idx + 1)
    lis_idx = [0] * (idx + 1)
    for i, a in enumerate(arr[::-1]):
        if dp2[~i] == idx:
            lis[idx] = a
            lis_idx[idx] = n - i - 1
            idx -= 1
    return lis_idx if return_idx else lis


def number_of_subsequences(arr: list[int], mod: int) -> int:
    """Count distinct subsequences modulo ``mod``.

    The count includes the empty subsequence. Equal values are handled with the
    standard last-occurrence DP recurrence.

    Args:
        arr: Input array.
        mod: Positive modulus for the result.

    Returns:
        Number of distinct subsequences modulo ``mod``, including the empty
        subsequence.

    Raises:
        ValueError: If ``mod`` is not positive.

    Time Complexity:
        ``O(n)``

    Space Complexity:
        ``O(k)`` where ``k`` is the number of distinct values.

    Examples:
        >>> # The distinct subsequences are: [], [1], [2], [1, 2], [2, 1], [1, 1], [1, 2, 1]. So the answer is 7.
        >>> number_of_subsequences([1, 2, 1], 100)
        7
    """
    if mod <= 0:
        raise ValueError('mod must be positive')
    dp = 1 % mod
    prev: dict[int, int] = {}
    for a in arr:
        previous_count = dp
        dp = (dp * 2 - prev.get(a, 0)) % mod
        prev[a] = previous_count
    return dp


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
