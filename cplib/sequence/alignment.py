#!/usr/bin/env python3

from collections.abc import Hashable, Sequence


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


def longest_common_subsequence_length_bitset(s: Sequence[Hashable], t: Sequence[Hashable]) -> int:
    """
    Return an LCS length using bit-parallel DP for hashable elements.

    Args:
        s: First sequence of hashable elements, for example str, bytes or ints.
        t: Second sequence of hashable elements with compatible equality/hashing.

    Returns:
        Length of an LCS. The actual subsequence is not restored.

    Notes:
        The shorter sequence is the bit axis. This is particularly useful for
        small alphabets. With many distinct symbols, masks can consume quadratic
        space in the shorter length; the ordinary LCS routine uses linear space
        and also accepts unhashable elements. That routine remains unchanged.

    Examples:
        >>> longest_common_subsequence_length_bitset('abracadabra', 'avada kedavra')
        7
        >>> longest_common_subsequence_length_bitset([1, 2, 1], [2, 1, 1])
        2

    Time Complexity:
        O((n + m) ceil(m / w)) word operations including mask construction,
        with expected constant-time hashing/equality; ``m`` is the shorter
        length, ``n`` the longer length, and ``w`` the integer digit width.

    Space Complexity:
        O(d ceil(m / w)) words for masks, where ``d`` is the number of distinct
        elements in the shorter sequence. Empty inputs use O(1) time/space.
    """
    if not s or not t:
        return 0
    if len(s) < len(t):
        s, t = t, s
    masks: dict[Hashable, int] = {}
    for i, value in enumerate(t):
        masks[value] = masks.get(value, 0) | (1 << i)
    row = 0
    for value in s:
        union = row | masks.get(value, 0)
        row = union & ~(union - ((row << 1) | 1))
    return row.bit_count()
