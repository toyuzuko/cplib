#!/usr/bin/env python3

"""Periodicity and repetition utilities for strings.

This module provides Lyndon factorization, minimum cyclic rotation queries,
and maximal run enumeration.
"""

from __future__ import annotations

from cplib.string.suffix import SuffixArray

__all__ = [
    "duval",
    "lyndon_factorization",
    "minimum_representation",
    "enumerate_runs",
]


def _validate_string(string: object) -> str:
    if not isinstance(string, str):
        raise ValueError("string must be a str")
    return string


def duval(input_string: str) -> list[tuple[int, int]]:
    """
    Compute the Lyndon factorization of a string.

    The returned factors are a sequence of non-increasing Lyndon words that
    partition the whole string. Each factor is represented as a half-open
    interval ``[l, r)``.

    Args:
        input_string: Input string to factorize.

    Returns:
        List of factor ranges ``(l, r)``. For the empty string, this returns
        ``[]``.

    Raises:
        ValueError: If ``input_string`` is not a string.

    Time Complexity:
        - ``O(n)``

    Space Complexity:
        - ``O(k)``, where ``k`` is the number of factors

    Examples:
        >>> duval("banana")
        [(0, 1), (1, 3), (3, 5), (5, 6)]
    """
    input_string = _validate_string(input_string)
    n: int = len(input_string)
    factors: list[tuple[int, int]] = []
    i: int = 0
    while i < n:
        j: int = i + 1
        k: int = i
        while j < n and input_string[k] <= input_string[j]:
            if input_string[k] < input_string[j]:
                k = i
            else:
                k += 1
            j += 1
        step = j - k
        while i <= k:
            factors.append((i, i + step))
            i += step
    return factors


def lyndon_factorization(input_string: str) -> list[str]:
    """
    Return the Lyndon factorization as substrings.

    Args:
        input_string: Input string to factorize.

    Returns:
        List of Lyndon factors as strings. For the empty string, this returns
        ``[]``.

    Raises:
        ValueError: If ``input_string`` is not a string.

    Time Complexity:
        - ``O(n)``

    Space Complexity:
        - ``O(n)``

    Examples:
        >>> lyndon_factorization("banana")
        ['b', 'an', 'an', 'a']
    """
    factors: list[str] = []
    for left, right in duval(input_string):
        factors.append(input_string[left:right])
    return factors


def minimum_representation(input_string: str) -> int:
    """
    Return the index of the lexicographically minimum cyclic rotation.

    The returned index is the smallest starting position among all minimum
    rotations. For the empty string, this function returns ``0``.

    Args:
        input_string: Input string.

    Returns:
        Starting index of the minimum cyclic rotation.

    Raises:
        ValueError: If ``input_string`` is not a string.

    Time Complexity:
        - ``O(n)``

    Space Complexity:
        - ``O(n)``

    Examples:
        >>> minimum_representation("bbaaccaadd")
        2
    """
    input_string = _validate_string(input_string)
    n: int = len(input_string)
    if n == 0:
        return 0

    doubled = input_string + input_string
    i: int = 0
    answer: int = 0
    while i < n:
        answer = i
        j: int = i + 1
        k: int = i
        while j < 2 * n and doubled[k] <= doubled[j]:
            if doubled[k] < doubled[j]:
                k = i
            else:
                k += 1
            j += 1
        step: int = j - k
        while i <= k:
            i += step
    return answer


def enumerate_runs(input_string: str) -> list[tuple[int, int, int]]:
    """
    Enumerate all maximal runs (tandem repeats) in a string.

    A run is an interval with least period p and length at least 2*p. Its
    length need not be a multiple of p: "ababa" is a run of period 2.
    It cannot be extended by one character to either side while keeping p
    as a period.

    Args:
        input_string: The input string to analyze

    Returns:
        list[tuple[int, int, int]]: List of tuples (period, start, end) where:
            - period: The period length of the run
            - start: Starting position of the maximal run (0-indexed)
            - end: Ending position of the maximal run (exclusive)

    Notes:
        - Uses suffix arrays and LCP queries to find runs efficiently
        - A run with period p at position i means s[i:i+p] = s[i+p:i+2p]
        - The algorithm extends each potential run maximally in both directions
        - Avoids duplicate runs using a set to track seen configurations
        - Based on the fact that there are at most O(n) maximal runs in a string

    Examples:
        >>> # "abababab" has period 2 from position 0 to 8
        >>> enumerate_runs("abababab")
        [(2, 0, 8)]

        >>> enumerate_runs("aabaaab")
        [(1, 0, 2), (1, 3, 6)]

        >>> enumerate_runs("abcabcabc")
        [(3, 0, 9)]

    Space Complexity:
        O(n log n), including suffix-array LCP sparse tables.

    Time Complexity:
        O(n log n), including suffix-array construction and LCP preprocessing.
    """
    n = len(input_string)
    sa = SuffixArray(input_string)
    sa_rev = SuffixArray(input_string[::-1])
    runs: list[tuple[int, int, int]] = []
    vis: set[int] = set()
    lst = -1
    for p in range(1, n // 2 + 1):
        for i in range(0, n - p + 1, p):
            l = i - sa_rev.get_lcp(n - i - p, n - i)
            r = i - p + sa.get_lcp(i, i + p)
            if l > r or l == lst:
                continue
            if l * (2 * n) + r + 2 * p not in vis:
                vis.add(l * (2 * n) + r + 2 * p)
                runs.append((p, l, r + 2 * p))
            lst = l
    return runs
