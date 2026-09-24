import random
import unittest

from cplib.graph.matching import MaximumWeightMatching, MinimumWeightPerfectMatching, MatchingResult
from cplib.graph.matching import BipartiteMaximumMatching, BipartiteMaximumWeightMatching, BipartiteMinimumWeightMaximumMatching


def optimal_weight(n: int, edges: dict[tuple[int, int], int], perfect: bool) -> int | None:
    """Enumerate vertex subsets, independently of the blossom algorithm."""
    dp: list[int | None] = [None] * (1 << n)
    dp[0] = 0
    for mask in range(1, 1 << n):
        first_bit = mask & -mask
        u = first_bit.bit_length() - 1
        rest = mask ^ first_bit
        best = None if perfect else dp[rest]
        choices = rest
        while choices:
            bit = choices & -choices
            choices ^= bit
            v = bit.bit_length() - 1
            previous = dp[rest ^ bit]
            if previous is None or (u, v) not in edges:
                continue
            candidate = previous + edges[u, v]
            if best is None or (candidate < best if perfect else candidate > best):
                best = candidate
        dp[mask] = best
    return dp[-1]


class GeneralWeightedMatchingTest(unittest.TestCase):
    def check_result(self, n: int, edges: dict[tuple[int, int], int], result: MatchingResult, perfect: bool) -> None:
        expected = optimal_weight(n, edges, perfect)
        self.assertEqual(result.success, expected is not None)
        self.assertEqual(result.weight, expected)
        if not result.success:
            self.assertIsNone(result.edges)
            return
        vertices: set[int] = set()
        weight = 0
        for u, v in result.edges:
            self.assertTrue(0 <= u < v < n)
            self.assertNotIn(u, vertices)
            self.assertNotIn(v, vertices)
            vertices.update((u, v))
            weight += edges[u, v]
        self.assertEqual(weight, expected)
        if perfect:
            self.assertEqual(len(vertices), n)

    def test_repeated_solves_and_added_edges(self) -> None:
        solver = MaximumWeightMatching(4)
        solver.add_edge(0, 1, 1)
        solver.add_edge(2, 3, 1)
        self.assertEqual(solver.solve().weight, 2)
        solver.add_edge(0, 2, 9)
        solver.add_edge(1, 3, 9)
        self.assertEqual(solver.solve().weight, 18)
        self.assertEqual(solver.solve().weight, 18)

    def test_maximum_against_subset_enumeration(self) -> None:
        rng = random.Random(0)
        for n in range(10):
            for case in range(40):
                solver = MaximumWeightMatching(n)
                edges: dict[tuple[int, int], int] = {}
                scale = 1 if case % 3 else 1 << 180
                pairs = [(u, v) for u in range(n) for v in range(u + 1, n)]
                rng.shuffle(pairs)
                for batch in (pairs[:len(pairs) // 2], pairs[len(pairs) // 2:]):
                    for u, v in batch:
                        if rng.randrange(3) == 0:
                            continue
                        for _ in range(rng.randrange(1, 4)):
                            weight = rng.randrange(-5, 16) * scale
                            solver.add_edge(u, v, weight)
                            edges[u, v] = max(edges.get((u, v), weight), weight)
                    for _ in range(2):
                        self.check_result(n, edges, solver.solve(), perfect=False)

    def test_perfect_against_subset_enumeration(self) -> None:
        rng = random.Random(1)
        for n in range(0, 10, 2):
            for case in range(40):
                solver = MinimumWeightPerfectMatching(n)
                edges: dict[tuple[int, int], int] = {}
                scale = 1 if case % 3 else 1 << 180
                for u in range(n):
                    for v in range(u + 1, n):
                        if rng.randrange(3) == 0:
                            continue
                        for _ in range(rng.randrange(1, 4)):
                            cost = rng.randrange(16) * scale
                            solver.add_edge(u, v, cost)
                            edges[u, v] = min(edges.get((u, v), cost), cost)
                for _ in range(2):
                    self.check_result(n, edges, solver.solve(), perfect=True)

    def test_empty_and_invalid_inputs(self) -> None:
        self.check_result(0, {}, MinimumWeightPerfectMatching(0).solve(), perfect=True)
        self.check_result(2, {}, MinimumWeightPerfectMatching(2).solve(), perfect=True)
        for n in (-4, -3, -2, -1):
            with self.assertRaises(ValueError):
                MaximumWeightMatching(n)
            with self.assertRaises(ValueError):
                MinimumWeightPerfectMatching(n)
        for n in (1, 3, 5):
            with self.assertRaises(ValueError):
                MinimumWeightPerfectMatching(n)
        for solver in (MaximumWeightMatching(4), MinimumWeightPerfectMatching(4)):
            solver.add_edge(0, 1, 3)
            solver.add_edge(2, 3, 7)
            for u, v in ((-1, 0), (0, -1), (4, 0), (0, 4)):
                with self.assertRaises(IndexError):
                    solver.add_edge(u, v, 9)
            with self.assertRaises(ValueError):
                solver.add_edge(0, 0, 9)
            self.assertEqual(solver.solve().weight, 10)

    def test_bipartite_invalid_inputs_preserve_edges(self) -> None:
        for cls in (BipartiteMaximumMatching, BipartiteMaximumWeightMatching, BipartiteMinimumWeightMaximumMatching):
            for n1, n2 in ((-1, 0), (0, -1), (-1, -1)):
                with self.assertRaises(ValueError):
                    cls(n1, n2)
        plain = BipartiteMaximumMatching(2, 3)
        plain.add_edge(0, 1)
        for u, v in ((-1, 0), (0, -1), (2, 0), (0, 3)):
            with self.assertRaises(IndexError):
                plain.add_edge(u, v)
        self.assertEqual(plain.solve().edges, [(0, 1)])
        self.assertEqual(BipartiteMaximumMatching(0, 3).solve().weight, 0)
        for cls in (BipartiteMaximumWeightMatching, BipartiteMinimumWeightMaximumMatching):
            weighted = cls(2, 3)
            weighted.add_edge(0, 1, 7)
            for u, v in ((-1, 0), (0, -1), (2, 0), (0, 3)):
                with self.assertRaises(IndexError):
                    weighted.add_edge(u, v, 11)
            self.assertEqual(weighted.solve().weight, 7)
        maximum = BipartiteMaximumWeightMatching(1, 1)
        with self.assertRaises(ValueError):
            maximum.add_edge(0, 0, -1)
        maximum.add_edge(0, 0, 0)
        self.assertEqual(maximum.solve().weight, 0)


if __name__ == '__main__':
    unittest.main()
