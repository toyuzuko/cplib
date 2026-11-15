'''Integer Lagrangian relaxation for exact-cardinality minimization.'''

from collections.abc import Callable


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
