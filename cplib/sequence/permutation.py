#!/usr/bin/env python3

from bisect import bisect_left
from collections.abc import Sequence

from cplib.datastructure.fenwicktree import FenwickTree
from cplib.tools.type import KeyT


def next_permutation(perm: list[int]) -> bool:
    """
    Find the next lexicographically greater permutation of a sequence.

    The sequence is modified in-place.

    Args:
        perm: The sequence to find next permutation.

    Returns:
        True if the sequence was modified to the next permutation,
        False if the sequence was already the largest possible permutation.

    Notes:
        Algorithm:
        1. Find largest i where perm[i-1] < perm[i]
        2. Find largest j where perm[j] > perm[i-1]
        3. Swap perm[i-1] and perm[j]
        4. Reverse perm[i:]

    Examples:
        >>> a = [1, 2, 3]
        >>> next_permutation(a)
        True
        >>> a
        [1, 3, 2]
        >>> next_permutation(a)
        True
        >>> a
        [2, 1, 3]

    Time Complexity:
        O(n)

    Space Complexity:
        O(1)

    Complexity Notation:
        ``n = len(perm)``.
    """
    n = len(perm)
    if n <= 1:
        return False
    i = n - 1
    while i > 0 and perm[i - 1] >= perm[i]:
        i -= 1
    if i == 0:
        return False
    j = n - 1
    while perm[j] <= perm[i - 1]:
        j -= 1
    perm[i - 1], perm[j] = perm[j], perm[i - 1]
    l, r = i, n - 1
    while l < r:
        perm[l], perm[r] = perm[r], perm[l]
        l += 1
        r -= 1
    return True


def prev_permutation(perm: list[int]) -> bool:
    """
    Find the previous lexicographically smaller permutation of a sequence.

    The sequence is modified in-place.

    Args:
        perm: The sequence to find previous permutation.

    Returns:
        True if the sequence was modified to the previous permutation,
        False if the sequence was already the smallest possible permutation.

    Notes:
        Algorithm:
        1. Find largest i where perm[i-1] > perm[i]
        2. Find largest j where perm[j] < perm[i-1]
        3. Swap perm[i-1] and perm[j]
        4. Reverse perm[i:]

    Examples:
        >>> a = [2, 1, 3]
        >>> prev_permutation(a)
        True
        >>> a
        [1, 3, 2]
        >>> prev_permutation(a)
        True
        >>> a
        [1, 2, 3]

    Time Complexity:
        O(n)

    Space Complexity:
        O(1)

    Complexity Notation:
        ``n = len(perm)``.
    """
    n = len(perm)
    if n <= 1:
        return False
    i = n - 1
    while i > 0 and perm[i - 1] <= perm[i]:
        i -= 1
    if i == 0:
        return False
    j = n - 1
    while perm[j] >= perm[i - 1]:
        j -= 1
    perm[i - 1], perm[j] = perm[j], perm[i - 1]
    l, r = i, n - 1
    while l < r:
        perm[l], perm[r] = perm[r], perm[l]
        l += 1
        r -= 1
    return True


def count_inversions(arr: Sequence[KeyT]) -> int:
    """
    Count inversions in a sequence.

    Args:
        arr: Input sequence. Elements must be mutually comparable.

    Returns:
        Number of pairs ``(i, j)`` such that ``i < j`` and ``arr[i] > arr[j]``.

    Time Complexity:
        O(n log n), where ``n = len(arr)``.

    Space Complexity:
        O(n)
    """
    if not arr:
        return 0
    values = sorted(arr)
    compressed = [values[0]]
    for value in values[1:]:
        if compressed[-1] != value:
            compressed.append(value)
    bit = FenwickTree(len(compressed))
    res = 0
    for i, value in enumerate(arr):
        rank = bisect_left(compressed, value)
        res += i - bit.sum(rank + 1)
        bit.add(rank, 1)
    return res
