#!/usr/bin/env python3

from collections.abc import Sequence


def edit_distance(s: Sequence[object], t: Sequence[object], insert_cost: int = 1, delete_cost: int = 1, replace_cost: int = 1) -> int:
    """
    Return the weighted edit distance between two sequences.

    Args:
        s: Source sequence.
        t: Target sequence.
        insert_cost: Cost to insert one element into ``s``.
        delete_cost: Cost to delete one element from ``s``.
        replace_cost: Cost to replace one element.

    Returns:
        Minimum total edit cost to transform ``s`` into ``t``.

    Raises:
        ValueError: If any operation cost is negative.

    Time Complexity:
        O(nm), where ``n = len(s)`` and ``m = len(t)``.

    Space Complexity:
        O(m)
    """
    if insert_cost < 0 or delete_cost < 0 or replace_cost < 0:
        raise ValueError('operation costs must be non-negative')
    m = len(t)
    prev = [j * insert_cost for j in range(m + 1)]
    for i, s_value in enumerate(s, 1):
        cur = [0] * (m + 1)
        cur[0] = i * delete_cost
        for j, t_value in enumerate(t, 1):
            if s_value == t_value:
                replace = prev[j - 1]
            else:
                replace = prev[j - 1] + replace_cost
            insert = cur[j - 1] + insert_cost
            delete = prev[j] + delete_cost
            cur[j] = min(insert, delete, replace)
        prev = cur
    return prev[m]


def longest_common_subsequence_length(s: Sequence[object], t: Sequence[object]) -> int:
    """
    Return the length of the longest common subsequence of two sequences.

    Args:
        s: First sequence.
        t: Second sequence.

    Returns:
        Length of an LCS of ``s`` and ``t``.

    Time Complexity:
        O(nm), where ``n = len(s)`` and ``m = len(t)``.

    Space Complexity:
        O(m)
    """
    m = len(t)
    prev = [0] * (m + 1)
    for s_value in s:
        cur = [0] * (m + 1)
        for j, t_value in enumerate(t, 1):
            if s_value == t_value:
                cur[j] = prev[j - 1] + 1
            elif prev[j] >= cur[j - 1]:
                cur[j] = prev[j]
            else:
                cur[j] = cur[j - 1]
        prev = cur
    return prev[m]
