#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Sequence


def fibonacci_number(n: int, f0: int = 0, f1: int = 1) -> int:
    """
    Return the n-th term of a Fibonacci-type sequence.

    The sequence is defined by ``F(0) = f0``, ``F(1) = f1``, and
    ``F(n + 2) = F(n + 1) + F(n)``.

    Args:
        n: Index of the term.
        f0: Initial value ``F(0)``.
        f1: Initial value ``F(1)``.

    Returns:
        The value ``F(n)``.

    Raises:
        ValueError: If ``n`` is negative.

    Time Complexity:
        O(log(n + 1)) arithmetic operations. Integer arithmetic is not
        constant-time for large terms.

    Space Complexity:
        O(1) integer variables, excluding their bit lengths.
    """
    if n < 0:
        raise ValueError('n must be non-negative')

    a, b = 0, 1
    for bit in range(n.bit_length() - 1, -1, -1):
        c = a * ((b << 1) - a)
        d = a * a + b * b
        if (n >> bit) & 1:
            a, b = d, c + d
        else:
            a, b = c, d
    return f0 * (b - a) + f1 * a


def minimum_coin_count(coins: Sequence[int], amount: int) -> int:
    """
    Return the minimum number of unlimited coins needed to make ``amount``.

    Args:
        coins: Available positive coin values. Each value can be used any
            number of times.
        amount: Target total amount.

    Returns:
        Minimum coin count, or ``-1`` if ``amount`` cannot be made.

    Raises:
        ValueError: If ``amount`` is negative or a coin value is not positive.

    Time Complexity:
        O(amount * n), where ``n`` is ``len(coins)``.

    Space Complexity:
        O(amount)
    """
    if amount < 0:
        raise ValueError('amount must be non-negative')
    inf = amount + 1
    dp = [inf] * (amount + 1)
    dp[0] = 0
    for coin in coins:
        if coin <= 0:
            raise ValueError('coin values must be positive')
        for value in range(coin, amount + 1):
            cand = dp[value - coin] + 1
            if cand < dp[value]:
                dp[value] = cand
    return -1 if dp[amount] == inf else dp[amount]


def matrix_chain_multiplication_cost(dimensions: Sequence[tuple[int, int]]) -> int:
    """
    Return the minimum scalar multiplication count for a matrix chain.

    Args:
        dimensions: Matrix dimensions ``(rows, columns)`` in multiplication
            order. Adjacent dimensions must be compatible.

    Returns:
        Minimum scalar multiplication count.

    Raises:
        ValueError: If any dimension is non-positive or adjacent matrices are
            incompatible.

    Time Complexity:
        O(n^3), where ``n = len(dimensions)``.

    Space Complexity:
        O(n^2)
    """
    n = len(dimensions)
    if n <= 1:
        if n == 1 and (dimensions[0][0] <= 0 or dimensions[0][1] <= 0):
            raise ValueError('matrix dimensions must be positive')
        return 0
    p = [0] * (n + 1)
    p[0] = dimensions[0][0]
    for i, (rows, cols) in enumerate(dimensions):
        if rows <= 0 or cols <= 0:
            raise ValueError('matrix dimensions must be positive')
        if i and dimensions[i - 1][1] != rows:
            raise ValueError('adjacent matrices must be compatible')
        p[i + 1] = cols

    dp = [[0] * n for _ in range(n)]
    for width in range(2, n + 1):
        for left in range(n - width + 1):
            right = left + width - 1
            best = dp[left + 1][right] + p[left] * p[left + 1] * p[right + 1]
            for mid in range(left + 1, right):
                cost = dp[left][mid] + dp[mid + 1][right] + p[left] * p[mid + 1] * p[right + 1]
                if cost < best:
                    best = cost
            dp[left][right] = best
    return dp[0][n - 1]


def optimal_binary_search_tree_cost(p: Sequence[float], q: Sequence[float]) -> float:
    """
    Return the minimum expected search cost of an optimal binary search tree.

    Args:
        p: Successful-search probabilities for sorted keys.
        q: Unsuccessful-search probabilities for the gaps. Its length must be
            ``len(p) + 1``.

    Returns:
        Minimum expected search cost.

    Raises:
        ValueError: If ``len(q) != len(p) + 1``.

    Time Complexity:
        O(n^2), where ``n = len(p)``.

    Space Complexity:
        O(n^2)
    """
    n = len(p)
    if len(q) != n + 1:
        raise ValueError('q must have len(p) + 1 elements')

    prefix_p = [0.0] * (n + 1)
    prefix_q = [0.0] * (n + 2)
    for i, value in enumerate(p):
        prefix_p[i + 1] = prefix_p[i] + value
    for i, value in enumerate(q):
        prefix_q[i + 1] = prefix_q[i] + value

    dp = [[0.0] * (n + 1) for _ in range(n + 1)]
    opt = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][i] = q[i]
        opt[i][i] = i

    for width in range(1, n + 1):
        for left in range(n - width + 1):
            right = left + width
            weight = (prefix_p[right] - prefix_p[left]) + (prefix_q[right + 1] - prefix_q[left])
            start = opt[left][right - 1]
            end = opt[left + 1][right] if left + 1 <= right else right - 1
            if start < left:
                start = left
            if end > right - 1:
                end = right - 1
            best = float('inf')
            best_root = start
            for root in range(start, end + 1):
                cost = dp[left][root] + dp[root + 1][right] + weight
                if cost < best:
                    best = cost
                    best_root = root
            dp[left][right] = best
            opt[left][right] = best_root
    return dp[0][n]


def min_plus_convolution_convex_convex(a: Sequence[int], b: Sequence[int]) -> list[int]:
    """
    Compute min-plus convolution of two discrete convex integer sequences.

    Args:
        a: Sequence with nondecreasing adjacent differences.
        b: Sequence with nondecreasing adjacent differences.

    Returns:
        ``c[k] = min(a[i] + b[j] for i + j == k)`` over valid indices,
        or an empty list if either input is empty. Negative values and equal
        slopes are supported. This is not a general min-plus convolution.

    Raises:
        ValueError: If either sequence is not convex, even if the other is empty.

    Notes:
        Merge the sorted adjacent differences. Taking the smallest ``k`` slopes
        respects each sequence's prefix constraint, yielding the minimum cost
        at index ``k``. This integer specialization avoids floating-point slope
        comparisons and accumulation error.

    Examples:
        >>> min_plus_convolution_convex_convex([3, 1, 2], [0, 0, 4])
        [3, 1, 1, 2, 6]
        >>> min_plus_convolution_convex_convex([], [5])
        []

    Time Complexity:
        O(n + m) integer arithmetic/comparison operations.

    Space Complexity:
        O(n + m) for the result; O(1) auxiliary integer variables.
    """
    for values in (a, b):
        for i in range(2, len(values)):
            if values[i] - values[i - 1] < values[i - 1] - values[i - 2]:
                raise ValueError('inputs must be convex')
    if not a or not b:
        return []
    result = [a[0] + b[0]]
    i = j = 1
    while i < len(a) and j < len(b):
        da = a[i] - a[i - 1]
        db = b[j] - b[j - 1]
        if da <= db:
            result.append(result[-1] + da)
            i += 1
        else:
            result.append(result[-1] + db)
            j += 1
    while i < len(a):
        result.append(result[-1] + a[i] - a[i - 1])
        i += 1
    while j < len(b):
        result.append(result[-1] + b[j] - b[j - 1])
        j += 1
    return result
