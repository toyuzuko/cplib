from collections import deque
import itertools
import math
import random
import unittest

from cplib.algorithm.bisearch import ParallelBinarySearch, float_binary_search
from cplib.algorithm.knapsack import bounded_knapsack_small_values, knapsack
from cplib.algorithm.mo import HilbertMo, Mo, RollbackMo
from cplib.algorithm.sat import CnfSatSolver, ThreeSatSolver, TwoSatSolver
from cplib.algorithm.sort import bubble_sort, counting_sort, insertion_sort, intro_sort, merge_sort, partition, quick_sort, selection_sort, shell_sort


class AlgorithmContractsTest(unittest.TestCase):
    def test_float_search_extreme_endpoints(self) -> None:
        cases = [(1e308, 1.6e308, 1.2e308), (-1.6e308, -1e308, -1.2e308), (-1.6e308, 1.6e308, 1e307), (0.0, 1e-320, 5e-321)]
        for left, right, boundary in cases:
            for ng, ok in ((left, right), (right, left)):
                increasing = ng < ok
                def check(x: float) -> bool:
                    self.assertTrue(math.isfinite(x))
                    self.assertTrue(left <= x <= right)
                    return x >= boundary if increasing else x <= boundary
                result = float_binary_search(ng, ok, check)
                self.assertTrue(check(result))
                self.assertTrue(math.isclose(result, boundary, rel_tol=1e-14, abs_tol=math.ulp(boundary)))
        for invalid in (math.inf, -math.inf, math.nan):
            with self.assertRaises(ValueError):
                float_binary_search(invalid, 1.0, lambda _: True)
        with self.assertRaises(ValueError):
            float_binary_search(0.0, 1.0, lambda _: True, iterations=-1)

    def test_sorting_and_custom_gaps(self) -> None:
        rng = random.Random(0)
        for _ in range(130):
            values = [rng.randrange(-5, 6) for _ in range(rng.randrange(45))]
            expected = sorted(values)
            self.assertEqual(counting_sort(values, min_value=-5), expected)
            for gaps in (None, [], [2], [100], [1, 4, 3]):
                self.assertEqual(shell_sort(values, gaps=gaps), expected)
            for sort in (insertion_sort, bubble_sort, selection_sort, quick_sort):
                self.assertEqual(sort(values), expected)
            for threshold in (1, 3, 16):
                self.assertEqual(intro_sort(values, lambda a, b: a < b, threshold), expected)
                self.assertEqual(merge_sort(values, lambda a, b: a < b, threshold), expected)
            records = list(enumerate(values))
            self.assertEqual(merge_sort(records, lambda a, b: a[1] < b[1]), sorted(records, key=lambda a: a[1]))
            for gap in (1, 3, 100):
                result = insertion_sort(values, gap=gap)
                for offset in range(min(gap, len(values))):
                    self.assertEqual(result[offset::gap], sorted(values[offset::gap]))
            if values:
                left = rng.randrange(len(values))
                right = rng.randrange(left + 1, len(values) + 1)
                result, pivot = partition(values, left=left, right=right)
                self.assertEqual(result[:left], values[:left])
                self.assertEqual(result[right:], values[right:])
                self.assertEqual(sorted(result[left:right]), sorted(values[left:right]))
                self.assertTrue(all(x <= result[pivot] for x in result[left:pivot]))
                self.assertTrue(all(x > result[pivot] for x in result[pivot + 1:right]))
        self.assertEqual(shell_sort([2, 1, 3], gaps=[2]), [1, 2, 3])
        with self.assertRaises(ValueError):
            counting_sort([], max_value=0, min_value=1)
        with self.assertRaises(ValueError):
            merge_sort([], lambda a, b: a < b, threshold=-1)

    def test_sat_against_all_assignments(self) -> None:
        rng = random.Random(0)
        for width in (2, 3, None):
            for _ in range(180):
                n = rng.randrange(1, 7)
                clauses = [[(rng.randrange(n), bool(rng.randrange(2))) for _ in range(width if width is not None else rng.randrange(9))] for _ in range(rng.randrange(20))]
                if width == 2:
                    solver = TwoSatSolver(n=n)
                    for (i, f), (j, g) in clauses:
                        solver.add_clause(i, f, j, g)
                elif width == 3:
                    solver = ThreeSatSolver(n=n)
                    for (i, f), (j, g), (k, h) in clauses:
                        solver.add_clause(i, f, j, g, k, h)
                else:
                    solver = CnfSatSolver(n=n)
                    for clause in clauses:
                        solver.add_clause(clause)
                expected = any(all(any(values[i] == value for i, value in clause) for clause in clauses) for values in itertools.product((False, True), repeat=n))
                for _ in range(2):
                    result = solver.solve()
                    self.assertEqual(bool(result), expected)
                    if expected:
                        assert result.assignment is not None
                        self.assertEqual(len(result.assignment), n)
                        self.assertTrue(all(type(value) is bool for value in result.assignment))
                        self.assertTrue(all(any(result.assignment[i] == value for i, value in clause) for clause in clauses))
                    else:
                        self.assertIsNone(result.assignment)

    def test_sat_boolean_assignments(self) -> None:
        for cls in (TwoSatSolver, ThreeSatSolver, CnfSatSolver):
            for n in (0, 3):
                result = cls(n).solve()
                self.assertTrue(result.satisfiable)
                self.assertEqual(result.assignment, [False] * n)
                assert result.assignment is not None
                self.assertTrue(all(type(value) is bool for value in result.assignment))
        two, three, cnf = TwoSatSolver(6), ThreeSatSolver(6), CnfSatSolver(6)
        two.add_clause(0, True, 0, True)
        three.add_clause(0, True, 0, True, 0, True)
        cnf.add_clause([(0, True)])
        cnf.add_clause([(i, False) for i in range(1, 6)])
        for solver in (two, three, cnf):
            result = solver.solve()
            assert result.assignment is not None
            self.assertEqual(len(result.assignment), 6)
            self.assertIs(result.assignment[0], True)
            self.assertTrue(all(type(value) is bool for value in result.assignment))

    def test_sat_invalid_clauses_leave_solver_usable(self) -> None:
        for cls in (TwoSatSolver, ThreeSatSolver, CnfSatSolver):
            with self.assertRaises(ValueError):
                cls(n=-1)
            self.assertTrue(cls(n=0).solve())
        for invalid in (-1, 1):
            two = TwoSatSolver(n=1)
            three = ThreeSatSolver(n=1)
            cnf = CnfSatSolver(n=1)
            with self.assertRaises(IndexError):
                two.add_clause(0, True, invalid, False)
            with self.assertRaises(IndexError):
                three.add_clause(0, True, 0, False, invalid, True)
            with self.assertRaises(IndexError):
                cnf.add_clause([(0, True), (invalid, False)])
            two.add_clause(0, False, 0, False)
            three.add_clause(0, False, 0, False, 0, False)
            cnf.add_clause([(0, False)])
            for solver in (two, three, cnf):
                self.assertEqual(solver.solve().assignment, [False])

    def test_mo_callbacks_and_repeated_execution(self) -> None:
        rng = random.Random(0)
        for n in range(16):
            queries = [(l, r) for l in range(n + 1) for r in range(l, n + 1)]
            rng.shuffle(queries)
            for cls in (Mo, HilbertMo):
                mo = cls(n)
                for l, r in queries:
                    mo.add_query(l, r)
                for _ in range(2):
                    active: deque[int] = deque()
                    def remove_left(i: int) -> None:
                        self.assertEqual(active.popleft(), i)
                    def remove_right(i: int) -> None:
                        self.assertEqual(active.pop(), i)
                    self.assertEqual(mo.run(active.appendleft, active.append, remove_left, remove_right, lambda _: tuple(active)), [tuple(range(l, r)) for l, r in queries])
            for block in (None, 1, 4, 100):
                rollback_mo = RollbackMo(n, block_size=block)
                for l, r in queries:
                    rollback_mo.add_query(l, r)
                active_list: list[int] = []
                def rollback(snapshot: int) -> None:
                    del active_list[snapshot:]
                for _ in range(2):
                    self.assertEqual(rollback_mo.run(active_list.append, lambda: len(active_list), rollback, lambda _: tuple(sorted(active_list))), [tuple(range(l, r)) for l, r in queries])
                    self.assertEqual(active_list, [])

    def test_parallel_search_and_negative_capacity(self) -> None:
        rng = random.Random(0)
        for n in range(25):
            values = [rng.randrange(5) for _ in range(n)]
            prefix = [0]
            for value in values:
                prefix.append(prefix[-1] + value)
            targets = [rng.randrange(-2, sum(values) + 3) for _ in range(30)]
            pbs = ParallelBinarySearch(n)
            for _ in targets:
                pbs.add_query()
            state = 0
            def reset() -> None:
                nonlocal state
                state = 0
            def apply(i: int) -> None:
                nonlocal state
                state += values[i]
            expected = [next((i for i, value in enumerate(prefix) if value >= target), n + 1) for target in targets]
            for _ in range(2):
                self.assertEqual(pbs.run(reset, apply, lambda i: state >= targets[i]), expected)
        for restore in (False, True):
            with self.assertRaises(ValueError):
                knapsack([], -1, restore=restore)
        with self.assertRaises(ValueError):
            bounded_knapsack_small_values([], -1)


if __name__ == '__main__':
    unittest.main()
