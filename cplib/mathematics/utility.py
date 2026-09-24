#!/usr/bin/env python3

"""Integer helpers; complexity counts integer operations, not bit operations."""

from collections.abc import Iterator


def absolute(x: int) -> int:
    """
    Return the absolute value of an arbitrary integer.

    Args:
        x (int): The integer.

    Returns:
        int: The absolute value of the integer.

    Examples:
        >>> absolute(-5)
        5

    Time Complexity:
        O(1)

    Space Complexity:
        O(1) auxiliary space
    """
    return abs(x)


def sign(x: int) -> int:
    """
    Return -1, 0, or 1 according to the sign of an arbitrary integer.

    Args:
        x (int): The integer.

    Returns:
        int: The sign of the integer (-1, 0, or 1).

    Examples:
        >>> sign(-5)
        -1
        >>> sign(0)
        0
        >>> sign(5)
        1

    Time Complexity:
        O(1)

    Space Complexity:
        O(1) auxiliary space
    """
    return (x > 0) - (x < 0)


def clamp(x: int, a: int, b: int) -> int:
    """
    Clamp an arbitrary integer to the inclusive interval [a, b].

    Args:
        x (int): The integer to clamp.
        a (int): The lower bound.
        b (int): The upper bound.

    Returns:
        int: The clamped value.

    Raises:
        ValueError: If a > b.

    Examples:
        >>> clamp(5, 1, 10)
        5
        >>> clamp(0, 1, 10)
        1

    Time Complexity:
        O(1)

    Space Complexity:
        O(1) auxiliary space
    """
    if a > b:
        raise ValueError('lower bound must not exceed upper bound')
    return min(max(x, a), b)


def xorshift64(state: int) -> int:
    """
    Advance a 64-bit xorshift generator by one step.

    Args:
        state: Unsigned 64-bit state. Zero remains zero.

    Returns:
        The next internal state.

    Raises:
        ValueError: If state is outside [0, 2**64).

    Time Complexity:
        ``O(1)``.

    Space Complexity:
        O(1) auxiliary space
    """
    if not 0 <= state < 1 << 64:
        raise ValueError('state must be an unsigned 64-bit integer')
    state ^= (state << 7) & ((1 << 64) - 1)
    state ^= state >> 9
    return state


def generate_quotient(n: int) -> Iterator[tuple[int, int, int]]:
    """
    Generates all distinct quotients of floor(n/i) for i in range [1, n].

    This function efficiently iterates through all distinct values of floor(n/i)
    for i = 1, 2, ..., n by grouping consecutive values of i that produce the
    same quotient. This is useful for algorithms that need to process all
    distinct quotients without iterating through every divisor.

    Args:
        n: Nonnegative dividend. Zero yields no ranges.

    Yields:
        tuple[int, int, int]: A tuple (q, l, r) where:
            - q: The quotient floor(n/i) for all i in range [l, r)
            - l: The left boundary of the range (inclusive)
            - r: The right boundary of the range (exclusive)

    Raises:
        ValueError: If n is negative, raised when the iterator is consumed.

    Examples:
        >>> list(generate_quotient(10))
        [(1, 6, 11), (2, 4, 6), (3, 3, 4), (5, 2, 3), (10, 1, 2)]

        This means:
        - floor(10/6) through floor(10/10) = 1 for i in range [6, 11)
        - floor(10/4) = floor(10/5) = 2 for i in range [4, 6)
        - floor(10/3) = 3 for i in range [3, 4)
        - floor(10/2) = 5 for i in range [2, 3)
        - floor(10/1) = 10 for i in range [1, 2)

    Time Complexity:
        ``O(sqrt(n))``

    Space Complexity:
        O(1) auxiliary space
    """
    if n < 0:
        raise ValueError('n must be nonnegative')
    r = n
    while r:
        q = n // r
        l = n // (q + 1)
        yield q, l + 1, r + 1
        r = l
