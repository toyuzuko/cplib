'''Bounded Monge-DAG oracle tests, not a full-size ABC355 G solver.'''

from collections.abc import Callable, Sequence
from itertools import combinations
import random
import unittest

from cplib.algorithm.dp import aliens_minimize


def center_oracle(weights: Sequence[int]) -> Callable[[int], tuple[int, int]]:
    n = len(weights)
    costs = [[0] * (n + 2) for _ in range(n + 2)]
    for j in range(1, n + 1):
        costs[0][j] = sum(weights[y - 1] * (j - y) for y in range(1, j))
    for i in range(1, n + 1):
        costs[i][n + 1] = sum(weights[y - 1] * (y - i) for y in range(i, n + 1))
        for j in range(i + 1, n + 1):
            costs[i][j] = sum(weights[y - 1] * min(y - i, j - y) for y in range(i, j))

    def solve(penalty: int) -> tuple[int, int]:
        dp = [(0, 0)]
        for j in range(1, n + 2):
            # A path visits at least one center: the direct edge does not exist.
            dp.append(min(
                (dp[i][0] + costs[i][j] + penalty, dp[i][1] + 1)
                for i in range(1 if j == n + 1 else 0, j)
            ))
        return dp[-1]

    return solve


class AliensMongeContractTest(unittest.TestCase):
    def test_against_exhaustive_center_subsets(self) -> None:
        # ABC355 G's center-distance DAG is Monge. This small quadratic
        # callback tests a recurrence unrelated to spaced-element selection.
        # Full-size inputs additionally require online Monge optimization.
        rng = random.Random(355)
        for n in range(1, 9):
            for _ in range(8):
                weights = [rng.randrange(5) for _ in range(n)]
                weights[rng.randrange(n)] += 1
                solve = center_oracle(weights)
                for k in range(1, n + 1):
                    expected = min(
                        sum(p * min(abs(x - y) for x in centers)
                            for y, p in enumerate(weights))
                        for centers in combinations(range(n), k)
                    )
                    # -1 chooses every center; at N*sum(P)+1 the penalty for
                    # an extra edge exceeds any possible unpenalized saving.
                    actual = aliens_minimize(k + 1, -1, n * sum(weights) + 1, solve)
                    self.assertEqual(actual, expected, (weights, k))


if __name__ == '__main__':
    unittest.main()
