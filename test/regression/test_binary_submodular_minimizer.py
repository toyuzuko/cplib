import itertools
import random
import unittest

from cplib.graph import BinarySubmodularMinimizer, BinarySubmodularResult
from cplib.graph.base import Node


class TestBinarySubmodularMinimizer(unittest.TestCase):
    def test_empty_ties_and_reuse(self) -> None:
        self.assertEqual(BinarySubmodularMinimizer(0).solve(), BinarySubmodularResult(0, []))
        solver = BinarySubmodularMinimizer(1)
        initial = solver.solve()
        self.assertEqual(initial.cost, 0)
        self.assertIn(initial.assignment[0], (0, 1))
        solver.add_pairwise(Node(0), Node(0), -4, -100, -100, -6)
        self.assertEqual(solver.solve(), BinarySubmodularResult(-6, [1]))
        solver.add_unary(Node(0), 1, 4)
        updated = solver.solve()
        self.assertEqual(updated, BinarySubmodularResult(-3, [0]))
        updated.assignment[0] = 1
        self.assertEqual(solver.solve(), BinarySubmodularResult(-3, [0]))
        self.assertEqual(initial.cost, 0)

    def test_invalid_terms_do_not_modify_model(self) -> None:
        with self.assertRaises(ValueError):
            BinarySubmodularMinimizer(-1)
        solver = BinarySubmodularMinimizer(2)
        with self.assertRaises(IndexError):
            solver.add_unary(Node(-1), 0, -2)
        with self.assertRaises(IndexError):
            solver.add_pairwise(Node(2), Node(2), 1, 1, 1, 1)
        with self.assertRaises(IndexError):
            solver.add_pairwise(Node(0), Node(2), 1, 1, 1, 1)
        with self.assertRaises(ValueError):
            solver.add_pairwise(Node(0), Node(1), 8, 1, 2, -3)
        self.assertEqual(solver.solve().cost, 0)

    def test_flow_can_exceed_default_infinity(self) -> None:
        huge = 10**100
        solver = BinarySubmodularMinimizer(2)
        solver.add_unary(Node(0), -2 * huge, 0)
        solver.add_unary(Node(1), 0, -3 * huge)
        solver.add_pairwise(Node(0), Node(1), -huge, 4 * huge, -huge, -huge)
        self.assertEqual(solver.solve(), BinarySubmodularResult(-4 * huge, [1, 1]))

    def test_randomized_exhaustive_cost_and_witness(self) -> None:
        rng = random.Random(193259)
        for _ in range(350):
            n = rng.randrange(1, 8)
            solver = BinarySubmodularMinimizer(n)
            unary: list[tuple[int, int, int]] = []
            pairwise: list[tuple[int, int, tuple[int, int, int, int]]] = []
            for _ in range(rng.randrange(19)):
                v = rng.randrange(n)
                c0, c1 = rng.randrange(-12, 13), rng.randrange(-12, 13)
                solver.add_unary(Node(v), c0, c1)
                unary.append((v, c0, c1))
            for _ in range(rng.randrange(22)):
                u, v = rng.randrange(n), rng.randrange(n)
                c00, c10, c11 = (rng.randrange(-12, 13) for _ in range(3))
                c01 = c00 + c11 - c10 + rng.randrange(20)
                costs = (c00, c01, c10, c11)
                solver.add_pairwise(Node(u), Node(v), *costs)
                pairwise.append((u, v, costs))

            def evaluate(bits: tuple[int, ...]) -> int:
                return sum(c1 if bits[v] else c0 for v, c0, c1 in unary) + sum(
                    c[2 * bits[u] + bits[v]] for u, v, c in pairwise
                )

            result = solver.solve()
            bits = tuple(result.assignment)
            self.assertEqual(len(bits), n)
            self.assertTrue(all(b in (0, 1) for b in bits))
            self.assertEqual(result.cost, evaluate(bits))
            self.assertEqual(result.cost, min(evaluate(x) for x in itertools.product(range(2), repeat=n)))


if __name__ == '__main__':
    unittest.main()
