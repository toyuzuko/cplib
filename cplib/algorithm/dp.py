#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, Self, TypeVar

from cplib.tools.type import KeyT


class _OrderedAdditive(Protocol):
    def __add__(self, other: Self, /) -> Self: ...
    def __sub__(self, other: Self, /) -> Self: ...
    def __lt__(self, other: Self, /) -> bool: ...


ConvexValueT = TypeVar('ConvexValueT', bound=_OrderedAdditive)


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


def min_plus_convolution_convex_convex(a: Sequence[ConvexValueT], b: Sequence[ConvexValueT]) -> list[ConvexValueT]:
    """
    Compute min-plus convolution of two discrete convex sequences.

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
        at index ``k``. Values must support addition, subtraction, and a
        translation-invariant order. Use exact values, such as integers or
        fractions, to avoid round-off in comparisons of adjacent slopes.

    Examples:
        >>> min_plus_convolution_convex_convex([3, 1, 2], [0, 0, 4])
        [3, 1, 1, 2, 6]
        >>> min_plus_convolution_convex_convex([], [5])
        []
        >>> from fractions import Fraction
        >>> min_plus_convolution_convex_convex([Fraction(0), Fraction(1, 2)], [Fraction(1, 3)])
        [Fraction(1, 3), Fraction(5, 6)]

    Time Complexity:
        O(n + m) arithmetic/comparison operations.

    Space Complexity:
        O(n + m) for the result; O(1) auxiliary values.
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
        if not db < da:
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


def aliens_minimize(
    target_count: int,
    penalty_low: int,
    penalty_high: int,
    solve: Callable[[int], tuple[int, int]],
) -> int:
    '''Recover an exact-count minimum from a penalized solver (Alien Trick).

    Let ``f(k)`` be the original minimum cost for exactly k choices. Its
    feasible counts must form a contiguous interval, and the signed integer
    costs must be discretely convex: consecutive differences of ``f`` are
    nondecreasing. The caller must establish these conditions; this function
    cannot verify them from the callback.

    Args:
        target_count: Desired feasible count (non-negative).
        penalty_low: Inclusive lower integer penalty bound.
        penalty_high: Inclusive upper integer penalty bound.
        solve: For a penalty p, return ``(min_k(f(k) + p*k), k)`` with any
            attaining k. Both endpoints must bracket the target: the count
            returned at penalty_low is at least target_count, and the count
            returned at penalty_high is at most target_count.

    Returns:
        The exact cost ``f(target_count)``, not an attaining assignment.

    Raises:
        ValueError: If the target is negative, the interval is reversed,
            or the endpoint counts do not bracket the target.

    Notes:
        The callback need not use a particular tie rule and may skip the
        target count at every queried penalty. In that case the maximum
        of the two bounds ``h(p) - p*target_count`` across the adjacent
        penalties where the count crosses the target is exact.

    Time Complexity:
        O(1 + log(penalty_high - penalty_low + 1)) callback evaluations and
        arithmetic operations, excluding integer bit complexity.

    Space Complexity:
        O(1), excluding the callback.

    Examples:
        >>> def penalized(p):
        ...     return min((4 - 2*k + p*k, k) for k in range(5))
        >>> aliens_minimize(2, -10, 10, penalized)
        0
    '''
    if target_count < 0:
        raise ValueError('target count must be non-negative')
    if penalty_low > penalty_high:
        raise ValueError('penalty interval must not be reversed')

    low, high = penalty_low, penalty_high
    low_cost, low_count = solve(low)
    high_cost, high_count = solve(high) if low < high else (low_cost, low_count)
    if not high_count <= target_count <= low_count:
        raise ValueError('endpoint counts must bracket the target count')
    if low_count == target_count:
        return low_cost - low * target_count
    if high_count == target_count:
        return high_cost - high * target_count

    while high - low > 1:
        middle = (low + high) // 2
        cost, count = solve(middle)
        if count == target_count:
            return cost - middle * target_count
        if count > target_count:
            low, low_cost = middle, cost
        else:
            high, high_cost = middle, cost
    # At least one of these adjacent integers supports f at target_count.
    return max(low_cost - low * target_count, high_cost - high * target_count)


def monotone_minima(
    n_rows: int, n_cols: int, value: Callable[[int, int], KeyT]
) -> list[int]:
    """
    Find the leftmost minimum column of every row of a monotone matrix.

    The leftmost row-minimum indices must be nondecreasing with the row
    index. This precondition is not checked. A rectangular Monge matrix is
    sufficient, but total monotonicity is not required. Values need only
    support a consistent strict ordering via ``<``; equivalent values tie
    in favor of the smaller column index.

    All entries of the rectangular domain must be defined, and ``value``
    must return stable values independently of evaluation order. Rows are
    evaluated in divide-and-conquer order, not increasing order. In
    particular, this is not an online Monge-DP solver: a callback must not
    depend on earlier rows being solved first. Triangular or staircase
    domains are not implicitly supported. Padding invalid entries is safe
    only if the resulting full matrix still satisfies these preconditions.

    Args:
        n_rows: Number of rows, indexed from zero.
        n_cols: Number of columns, indexed from zero.
        value: Callback returning the entry at a row and column.

    Returns:
        Leftmost minimum column indices in row order. For zero rows,
        returns an empty list without calling ``value``.

    Raises:
        ValueError: If either dimension is negative, or there are positive
            rows but no columns.

    Time Complexity:
        O(n_rows + n_cols * log(n_rows + 1)) callback evaluations and
        comparisons, assuming each costs O(1).

    Space Complexity:
        O(n_rows) for the result and O(log(n_rows + 1)) auxiliary space.

    Examples:
        >>> monotone_minima(4, 5, lambda i, j: (i - j) ** 2)
        [0, 1, 2, 3]
        >>> monotone_minima(3, 4, lambda i, j: 0)
        [0, 0, 0]
        >>> monotone_minima(0, 0, lambda i, j: 0)
        []
    """
    if n_rows < 0 or n_cols < 0:
        raise ValueError('matrix dimensions must be non-negative')
    if not n_rows:
        return []
    if not n_cols:
        raise ValueError('positive rows require at least one column')

    result = [0] * n_rows
    stack = [(0, n_rows, 0, n_cols)]
    while stack:
        row_lo, row_hi, col_lo, col_hi = stack.pop()
        row = (row_lo + row_hi) // 2
        best_col = col_lo
        best_value = value(row, col_lo)
        for col in range(col_lo + 1, col_hi):
            candidate = value(row, col)
            if candidate < best_value:
                best_col = col
                best_value = candidate
        result[row] = best_col
        if row + 1 < row_hi:
            stack.append((row + 1, row_hi, best_col, col_hi))
        if row_lo < row:
            stack.append((row_lo, row, col_lo, best_col + 1))
    return result
