#!/usr/bin/env python3

from bisect import bisect_left


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
