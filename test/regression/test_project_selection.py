import random
import unittest

from cplib.graph import maximum_weight_closure


class MaximumWeightClosureTest(unittest.TestCase):
    def check_exhaustive(self, profits, implications):
        n = len(profits)
        best = 0
        for mask in range(1 << n):
            if all(not (mask >> u & 1) or mask >> v & 1 for u, v in implications):
                best = max(best, sum(p for u, p in enumerate(profits) if mask >> u & 1))
        result = maximum_weight_closure(profits, implications)
        self.assertEqual(result.profit, best)
        selected = set(result.selected)
        self.assertEqual(result.selected, sorted(selected))
        self.assertTrue(all(u not in selected or v in selected for u, v in implications))
        self.assertEqual(sum(profits[u] for u in selected), best)
        self.assertEqual(result, maximum_weight_closure(profits, implications))

    def test_random_exhaustive(self):
        rng = random.Random(8102026)
        for n in range(9):
            for _ in range(80):
                profits = [rng.randrange(-10, 11) for _ in range(n)]
                dependencies = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randrange(n * n + 1))] if n else []
                original = profits[:], dependencies[:]
                self.check_exhaustive(profits, dependencies)
                self.assertEqual((profits, dependencies), original)

    def test_boundaries_and_large_integers(self):
        for profits, implications in [([], []), ([0, 0], [(0, 1)]), ([-1, -2], []),
                ([8, -3, -10], [(0, 1)]), ([10**100, -(10**100 - 1)], [(0, 1)]),
                ([10**100, -10**101], [(0, 1)]), ([10, -3, -4], [(0, 1), (1, 2), (2, 0)]),
                ([10, -3], [(0, 0), (0, 1), (0, 1)])]:
            self.check_exhaustive(profits, implications)

    def test_invalid_endpoint(self):
        for dependencies in [[(-1, 0)], [(0, -1)], [(1, 0)], [(0, 1)]]:
            with self.assertRaises(IndexError):
                maximum_weight_closure([1], dependencies)
        with self.assertRaises(IndexError):
            maximum_weight_closure([], [(0, 0)])


if __name__ == '__main__':
    unittest.main()
