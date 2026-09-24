#!/usr/bin/env python3

from math import isqrt


def enumerate_primes(n: int) -> list[int]:
    """
    Enumerate primes up to ``n`` using a segmented sieve.

    Args:
        n: Inclusive upper bound; values below 2 give no primes.

    Returns:
        Primes ``p`` with ``p <= n``.

    Time Complexity:
        ``O(n log log n)``

    Space Complexity:
        ``O(sqrt(n) + S + pi(n))`` where ``S`` is the segment size.

    Complexity Notation:
        ``n`` is the inclusive upper bound.
    """
    _, primes = enumerate_primes_by_index(n, 1, 0)
    return primes


def enumerate_primes_by_index(n: int, a: int, b: int) -> tuple[int, list[int]]:
    """
    Count primes up to ``n`` and enumerate primes at selected indices.

    The returned list contains the primes ``p_i`` whose zero-based index ``i``
    in the increasing prime sequence satisfies ``i % a == b``. This matches
    Library Checker's ``enumerate_primes`` output format without storing every
    prime up to ``n``.

    Args:
        n: Inclusive upper bound; values below 2 give no primes.
        a: Positive modulus for selected prime indices.
        b: Remainder with 0 <= b < a.

    Returns:
        ``(count, primes)`` where ``count`` is the number of primes up to
        ``n`` and ``primes`` is the selected subsequence.

    Raises:
        ValueError: If a <= 0 or b is outside [0, a), even when n < 2.

    Time Complexity:
        ``O(n log log n)``

    Space Complexity:
        ``O(sqrt(n) + S + M)`` where ``S`` is the segment size and ``M`` is the
        number of selected primes.

    Complexity Notation:
        ``n`` is the inclusive upper bound.
    """
    if a <= 0 or not 0 <= b < a:
        raise ValueError('indices must satisfy a > 0 and 0 <= b < a')
    if n < 2:
        return 0, []

    selected: list[int] = []
    total = 1
    next_index = b
    if next_index == 0:
        selected.append(2)
        next_index += a

    limit = isqrt(n)
    is_small_prime = bytearray(b'\x01') * (limit + 1)
    is_small_prime[0] = 0
    is_small_prime[1] = 0
    for p in range(2, isqrt(limit) + 1):
        if is_small_prime[p]:
            is_small_prime[p * p::p] = b'\x00' * ((limit - p * p) // p + 1)
    odd_base_primes = [p for p in range(3, limit + 1, 2) if is_small_prime[p]]
    segment_size = 1 << 22

    low = 3
    while low <= n:
        high = min(n + 1, low + segment_size * 2)
        size = (high - low + 1) // 2
        is_prime = bytearray(b'\x01') * size

        for p in odd_base_primes:
            p2 = p * p
            if p2 >= high:
                break
            start = max(p2, ((low + p - 1) // p) * p)
            if start % 2 == 0:
                start += p
            idx = (start - low) // 2
            is_prime[idx::p] = b'\x00' * ((size - 1 - idx) // p + 1)

        count = is_prime.count(1)
        if next_index < total + count:
            rank = -1
            pos = -1
            while next_index < total + count:
                target_rank = next_index - total
                while rank < target_rank:
                    pos = is_prime.find(1, pos + 1)
                    rank += 1
                selected.append(low + pos * 2)
                next_index += a
        total += count
        low = high | 1

    return total, selected
