# verification-helper: PROBLEM https://atcoder.jp/contests/abc462/tasks/abc462_f

from cplib.algorithm.dp import aliens_minimize
from cplib.tools.fastio import FastIO


def minimum_changes(s: str, increase: int) -> int:
    n = len(s)
    target = s.count('ABC') + increase
    if target > n // 3:
        return -1
    costs = [(s[i] != 'A') + (s[i + 1] != 'B') + (s[i + 2] != 'C')
             for i in range(n - 2)]

    def solve(penalty: int) -> tuple[int, int]:
        # Starts must be at least three apart. Keep the preceding three
        # prefix optima; a tied optimum with fewer starts is sufficient.
        a_cost = b_cost = c_cost = 0
        a_count = b_count = c_count = 0
        for cost in costs:
            take_cost = a_cost + cost + penalty
            take_count = a_count + 1
            if take_cost < c_cost or (take_cost == c_cost and take_count < c_count):
                next_cost, next_count = take_cost, take_count
            else:
                next_cost, next_count = c_cost, c_count
            a_cost, b_cost, c_cost = b_cost, c_cost, next_cost
            a_count, b_count, c_count = b_count, c_count, next_count
        return c_cost, c_count

    # The all-cardinality cost curve is convex by the alternating-merge
    # argument in AtCoder's Alien Trick lecture, Section 5.1.
    # Costs lie in [0, 3], so -3*target-1 forces at least target starts;
    # penalty 1 selects none. The library then recovers the exact-count cost.
    return aliens_minimize(target, -3 * target - 1, 1, solve)


for _ in range(FastIO.read_int()):
    text = FastIO.read()
    FastIO.writeln(f'{minimum_changes(text, FastIO.read_int())}')
