import itertools
import random
import unittest
from collections.abc import Callable

from cplib.algorithm import aliens_minimize


def oracle(values: list[int], first: int, prefer_high: bool) -> Callable[[int], tuple[int, int]]:
    def solve(penalty: int) -> tuple[int, int]:
        signed = -1 if prefer_high else 1
        cost, count = min(
            (value + penalty * count, signed * count)
            for count, value in enumerate(values, start=first)
        )
        return cost, signed * count

    return solve


class TestAliensMinimize(unittest.TestCase):
    def test_adjacent_penalty_crossing_and_flat_ties(self) -> None:
        # If tied counts skip the target, either endpoint can be the exact bound.
        for prefer_high in (False, True):
            solve = oracle([20, 17, 14, 11, 8], 0, prefer_high)
            self.assertEqual(aliens_minimize(2, 2, 4, solve), 14)
            low = 3 if prefer_high else 2
            self.assertEqual(aliens_minimize(2, low, low + 1, solve), 14)

    def test_large_signed_costs_and_singleton(self) -> None:
        huge = 10**100
        solve = oracle([0, -huge, -huge], 3, True)
        self.assertEqual(aliens_minimize(4, -huge - 1, huge + 1, solve), -huge)
        seen: list[int] = []

        def singleton(p: int) -> tuple[int, int]:
            seen.append(p)
            return -9 + 3 * p, 3

        self.assertEqual(aliens_minimize(3, -7, -7, singleton), -9)
        self.assertEqual(seen, [-7])

    def test_invalid_bounds(self) -> None:
        solve = oracle([0, 1, 3], 0, False)
        for count, lo, hi in [(-1, -1, 0), (1, 3, 2), (1, 0, 3), (1, -4, -3), (3, -4, 4)]:
            with self.subTest(count=count, lo=lo, hi=hi), self.assertRaises(ValueError):
                aliens_minimize(count, lo, hi, solve)

    def test_random_convex_curves_and_endpoint_counts(self) -> None:
        rng = random.Random(462355)
        for _ in range(250):
            start = rng.randrange(5)
            slopes = sorted(rng.randint(-20, 20) for _ in range(rng.randrange(16)))
            values = list(itertools.accumulate(slopes, initial=rng.randint(-50, 50)))
            for prefer_high in (False, True):
                solve = oracle(values, start, prefer_high)
                for count, expected in enumerate(values, start=start):
                    self.assertEqual(aliens_minimize(count, -21, 21, solve), expected)
