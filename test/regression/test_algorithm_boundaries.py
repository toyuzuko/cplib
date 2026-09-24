from collections import deque
from fractions import Fraction
from functools import cache
import itertools
import random
import unittest

from cplib.algorithm.dp import fibonacci_number, matrix_chain_multiplication_cost
from cplib.algorithm.greedy import fractional_knapsack, maximum_profit
from cplib.algorithm.knapsack import KnapsackItem, bounded_knapsack_small_values, knapsack, KnapsackResult
from cplib.algorithm.search import sliding_puzzle_distance, solve_n_queens


class AlgorithmBoundariesTest(unittest.TestCase):
    def test_matrix_chain_against_all_splits(self) -> None:
        self.assertEqual(matrix_chain_multiplication_cost([(10**9, 10**9)] * 2), 10**27)
        self.assertEqual(matrix_chain_multiplication_cost([]), 0)
        rng = random.Random(0)
        for _ in range(120):
            dimensions = [rng.randrange(1, 30) * rng.choice([1, 10**10]) for _ in range(rng.randrange(2, 9))]

            @cache
            def solve(left: int, right: int) -> int:
                if right - left == 1:
                    return 0
                return min(solve(left, mid) + solve(mid, right) + dimensions[left] * dimensions[mid] * dimensions[right] for mid in range(left + 1, right))

            self.assertEqual(matrix_chain_multiplication_cost(list(zip(dimensions, dimensions[1:]))), solve(0, len(dimensions) - 1))

    def test_fractional_knapsack_against_extreme_points(self) -> None:
        rng = random.Random(0)
        for _ in range(150):
            items = [(rng.randrange(-10, 20), rng.randrange(1, 8)) for _ in range(rng.randrange(7))]
            capacity = rng.randrange(20)
            best = Fraction(0)
            for mask in range(1 << len(items)):
                weight = sum(w for i, (_, w) in enumerate(items) if mask >> i & 1)
                value = sum(v for i, (v, _) in enumerate(items) if mask >> i & 1)
                if weight > capacity:
                    continue
                best = max(best, Fraction(value))
                for i, (v, w) in enumerate(items):
                    if not (mask >> i & 1):
                        best = max(best, value + Fraction(v * min(w, capacity - weight), w))
            self.assertAlmostEqual(fractional_knapsack(items, capacity), float(best))
        self.assertEqual(fractional_knapsack([(-1, 1)], 1), 0.0)
        with self.assertRaises(ValueError):
            fractional_knapsack([(-1, 0)], 0)

    def test_bounded_knapsack_large_capacity_and_multiplicity(self) -> None:
        self.assertEqual(bounded_knapsack_small_values([KnapsackItem(1, 1, 1)], 1 << 125), 1)
        self.assertEqual(bounded_knapsack_small_values([KnapsackItem(1, 1, 10**18)], 10**18), 10**18)
        items = [KnapsackItem(3 * 10**40, 4, 1), KnapsackItem(2 * 10**40, 2, 2)]
        self.assertEqual(bounded_knapsack_small_values(items, 4 * 10**40), 4)
        for items in ([], [KnapsackItem(1, 0, 1)]):
            with self.assertRaises(ValueError):
                bounded_knapsack_small_values(items, 3, window=-1)
        with self.assertRaises(ValueError):
            bounded_knapsack_small_values([KnapsackItem(1, 0, -1)], 3)
        items = [KnapsackItem(3, 5, 1), KnapsackItem(2, 3, 2)]
        self.assertEqual(bounded_knapsack_small_values(items, 4), 6)
        self.assertEqual(bounded_knapsack_small_values(items, 4, window=0), 5)

    def test_knapsack_variants_against_enumeration(self) -> None:
        rng = random.Random(0)
        for _ in range(180):
            items = [KnapsackItem(rng.randrange(6), rng.randrange(-3, 9), rng.randrange(4)) for _ in range(rng.randrange(6))]
            capacity = rng.randrange(25)
            best = max(sum(item.value * c for item, c in zip(items, counts)) for counts in itertools.product(*(range(item.count + 1) for item in items)) if sum(item.weight * c for item, c in zip(items, counts)) <= capacity)
            self.assertEqual(bounded_knapsack_small_values(items, capacity), best)
            for threshold in (0, 40):
                self.assertEqual(knapsack(items, capacity, mitm_threshold=threshold), best)
                result = knapsack(items, capacity, restore=True, mitm_threshold=threshold)
                self.assertIsInstance(result, KnapsackResult)
                assert isinstance(result, KnapsackResult)
                self.assertEqual(result.value, best)
                self.assertEqual(sum(item.value * c for item, c in zip(items, result.chosen)), best)
                self.assertLessEqual(sum(item.weight * c for item, c in zip(items, result.chosen)), capacity)
                self.assertTrue(all(0 <= c <= item.count for item, c in zip(items, result.chosen)))

    def test_fibonacci_and_profit_against_direct_calculations(self) -> None:
        for f0, f1 in itertools.product(range(-3, 4), repeat=2):
            a, b = f0, f1
            for n in range(100):
                self.assertEqual(fibonacci_number(n, f0, f1), a)
                a, b = b, a + b
        rng = random.Random(0)
        for _ in range(100):
            prices = [rng.randrange(-100, 100) for _ in range(rng.randrange(2, 20))]
            self.assertEqual(maximum_profit(prices), max(prices[j] - prices[i] for j in range(len(prices)) for i in range(j)))

    def test_sliding_puzzle_against_breadth_first_search(self) -> None:
        rng = random.Random(0)
        for height, width in ((1, 4), (4, 1), (2, 3), (3, 2)):
            n = height * width
            for _ in range(2):
                target = tuple(rng.sample(range(n), n))
                distances = {target: 0}
                queue = deque([target])
                while queue:
                    state = queue.popleft()
                    z = state.index(0)
                    r, c = divmod(z, width)
                    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                        if not (0 <= nr < height and 0 <= nc < width):
                            continue
                        nz = nr * width + nc
                        following = list(state)
                        following[z], following[nz] = following[nz], following[z]
                        neighbor = tuple(following)
                        if neighbor not in distances:
                            distances[neighbor] = distances[state] + 1
                            queue.append(neighbor)
                for state in rng.sample(list(itertools.permutations(range(n))), min(35, len(distances) + 5)):
                    expected = distances.get(state, -1)
                    self.assertEqual(sliding_puzzle_distance(state, height, width, target), expected)
                    if expected > 0:
                        self.assertEqual(sliding_puzzle_distance(state, height, width, target, expected - 1), -1)
        for board, height, width, target, limit in (([], 0, 0, [], None), ([0], -1, -1, None, None), ([0], 1, 1, None, -1)):
            with self.assertRaises(ValueError):
                sliding_puzzle_distance(board, height, width, target, limit)
        with self.assertRaises(ValueError):
            solve_n_queens(-1)
        self.assertEqual(solve_n_queens(0), ())


if __name__ == '__main__':
    unittest.main()
