#!/usr/bin/env python3

from math import isqrt


def count_primes(n: int) -> int:
    """
    Count the number of primes up to n using Lucy DP algorithm.

    The Lucy DP algorithm (also known as Lucy_Hedgehog algorithm) efficiently counts
    primes by computing S(v, p), the count of primes <= p and integers > p in
    [2, v] with no prime factor <= p. Primes themselves are retained when
    sieving their composite multiples. The key insight is that we only need
    to compute S for O(sqrt(n)) values: {n/1, n/2, ..., n/sqrt(n)} and
    {1, 2, ..., sqrt(n)-1}.

    The algorithm works in two phases:
    1. Initialize S(v) = v - 1 for all required values (count of integers >= 2)
    2. For each prime p up to sqrt(n), update S(v) by removing composites divisible by p
       using the formula: S(v) -= S(v/p) - S(p-1)

    Args:
        n: Upper bound (inclusive) for counting primes

    Returns:
        Number of primes <= n; zero if n < 2.

    Examples:
        >>> count_primes(10)
        4

    Time Complexity:
        ``O(n^(3/4) / log n)``

    Space Complexity:
        ``O(sqrt(n))``

    Complexity Notation:
        ``n`` is the upper bound of the counted range.
    """
    if n < 2: return 0
    sqn = isqrt(n)
    vs = [n // i for i in range(1, sqn + 1)] + [i for i in range(1, n // sqn)[::-1]]
    s = {v: v - 1 for v in vs}
    is_prime = [True] * (sqn + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, sqn + 1):
        if is_prime[p]:
            for j in range(p * p, sqn + 1, p):
                is_prime[j] = False
            p2 = p * p
            for v in vs:
                if v < p2:
                    break
                s[v] -= s[v // p] - s[p - 1]
    return s[n]


def count_squarefrees(n: int) -> int:
    """
    Count square-free integers up to n.

    Counts the integers ``x`` with ``1 <= x <= n`` such that no perfect square
    greater than ``1`` divides ``x``.

    Args:
        n: Upper bound (inclusive).

    Returns:
        Number of square-free integers in ``[1, n]``; zero if n <= 0.

    Examples:
        >>> count_squarefrees(10)
        7

    Time Complexity:
        Roughly ``O(n^(2/5))`` with a precomputation of the Möbius function up to
        ``sqrt(n / n^(1/5))``.

    Notes:
        Uses the identity
        ``Q(n) = sum_{i>=1} mu(i) * floor(n / i^2)``
        together with a decomposition that evaluates large values of the Mertens
        function ``M(x) = sum_{i<=x} mu(i)`` in batches.

    Space Complexity:
        ``O(n^(2/5))``

    Complexity Notation:
        ``n`` is the upper bound of the counted range.
    """
    if n <= 0:
        return 0
    if n <= 33:
        sqn = isqrt(n)
        mobius = [1] * (sqn + 1)
        is_prime = [True] * (sqn + 1)
        is_prime[0] = is_prime[1] = False
        for p in range(2, sqn + 1):
            if not is_prime[p]:
                continue
            mobius[p] = -1
            for q in range(p * 2, sqn + 1, p):
                is_prime[q] = False
                mobius[q] *= -1
            p2 = p * p
            for q in range(p2, sqn + 1, p2):
                mobius[q] = 0
        return sum(mobius[i] * (n // (i * i)) for i in range(1, sqn + 1))

    split = max(1, int(n ** 0.2))
    limit = isqrt(n // split)
    mobius = [1] * (limit + 1)
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, limit + 1):
        if not is_prime[p]:
            continue
        mobius[p] = -1
        for q in range(p * 2, limit + 1, p):
            is_prime[q] = False
            mobius[q] *= -1
        p2 = p * p
        for q in range(p2, limit + 1, p2):
            mobius[q] = 0

    small = 0
    for i in range(1, limit + 1):
        small += mobius[i] * (n // (i * i))

    mertens_prefix = [0]
    total = 0
    for i in range(1, limit + 1):
        total += mobius[i]
        mertens_prefix.append(total)

    large_mertens: list[int] = []
    large_sum = 0
    for i in range(split - 1, 0, -1):
        x = isqrt(n // i)
        sqx = isqrt(x)
        mx = 1
        upto = x // (sqx + 1)
        for j in range(1, upto + 1):
            mx -= (x // j - x // (j + 1)) * mertens_prefix[j]
        for j in range(2, sqx + 1):
            y = x // j
            if y <= limit:
                mx -= mertens_prefix[y]
            else:
                mx -= large_mertens[split - j * j * i - 1]
        large_mertens.append(mx)
        large_sum += mx

    return small + large_sum - (split - 1) * mertens_prefix[-1]


def sum_of_primes(n: int) -> int:
    """
    Calculate the sum of all primes up to n using Lucy DP algorithm.

    Similar to count_primes, but instead of counting primes, we sum them.
    The algorithm maintains S(v, p), the sum of primes <= p and integers > p
    in [2, v] with no prime factor <= p. Primes themselves remain in the sum
    when their composite multiples are removed.

    The algorithm works in two phases:
    1. Initialize S(v) = v*(v+1)//2 - 1 for all required values (sum of integers 2 to v)
    2. For each prime p up to sqrt(n), update S(v) by removing sum of composites
       divisible by p using: S(v) -= p * (S(v/p) - S(p-1))

    Args:
        n: Upper bound (inclusive) for summing primes

    Returns:
        Sum of all primes <= n; zero if n < 2.

    Examples:
        >>> sum_of_primes(10)
        17

    Time Complexity:
        ``O(n^(3/4) / log n)``

    Space Complexity:
        ``O(sqrt(n))``

    Complexity Notation:
        ``n`` is the upper bound of the summed range.
    """
    if n < 2: return 0
    sqn = isqrt(n)
    vs = [n // i for i in range(1, sqn + 1)] + [i for i in range(1, n // sqn)[::-1]]
    s = {v: v * (v + 1) // 2 - 1 for v in vs}
    is_prime = [True] * (sqn + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, sqn + 1):
        if is_prime[p]:
            for j in range(p * p, sqn + 1, p):
                is_prime[j] = False
            p2 = p * p
            for v in vs:
                if v < p2:
                    break
                s[v] -= p * (s[v // p] - s[p - 1])
    return s[n]
