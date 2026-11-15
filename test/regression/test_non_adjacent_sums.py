#!/usr/bin/env python3

import itertools
import random
import unittest

from cplib.sequence import maximum_non_adjacent_sums, minimum_non_adjacent_sums


def brute(values):
    n = len(values)
    low = [None] * ((n + 1) // 2 + 1)
    high = low.copy()
    for mask in range(1 << n):
        if mask & (mask << 1):
            continue
        k = mask.bit_count()
        total = sum(value for i, value in enumerate(values) if mask >> i & 1)
        if low[k] is None or total < low[k]:
            low[k] = total
        if high[k] is None or total > high[k]:
            high[k] = total
    return low, high


def dp(values, choose):
    skip = [0]
    take = []
    for value in values:
        size = max(len(skip), len(take))
        next_skip = []
        for k in range(size):
            candidates = [a[k] for a in (skip, take) if k < len(a) and a[k] is not None]
            next_skip.append(choose(candidates) if candidates else None)
        take = [None] + [value + x if x is not None else None for x in skip]
        skip = next_skip
    return [choose(a[k] for a in (skip, take) if k < len(a) and a[k] is not None) for k in range((len(values) + 1) // 2 + 1)]


class NonAdjacentSumsTests(unittest.TestCase):
    def check(self, values):
        original = list(values)
        low, high = brute(values)
        self.assertEqual(minimum_non_adjacent_sums(values), low, values)
        self.assertEqual(maximum_non_adjacent_sums(values), high, values)
        self.assertEqual(list(values), original)

    def test_exhaustive(self):
        for n in range(9):
            for values in itertools.product((-2, 0, 3), repeat=n):
                self.check(values)

    def test_adversarial(self):
        for n in range(16):
            for values in ([0] * n, [7] * n, [-7] * n, list(range(n)), list(range(n, 0, -1)), [(-1) ** i * 10 ** (i + 20) for i in range(n)]):
                self.check(values)

    def test_random_dp(self):
        rng = random.Random(218464)
        for _ in range(200):
            values = [rng.randrange(-100, 101) for _ in range(rng.randrange(150))]
            low = minimum_non_adjacent_sums(values)
            high = maximum_non_adjacent_sums(values)
            self.assertEqual(low, dp(values, min))
            self.assertEqual(high, dp(values, max))
            self.assertEqual(low, [-x for x in maximum_non_adjacent_sums([-x for x in values])])
            self.assertEqual(low, minimum_non_adjacent_sums(values[::-1]))
            self.assertEqual(high, maximum_non_adjacent_sums(values[::-1]))

    def test_large(self):
        n = 100_000
        self.assertEqual(minimum_non_adjacent_sums([1] * n), list(range(n // 2 + 1)))
        self.assertEqual(maximum_non_adjacent_sums([-1] * n), [-k for k in range(n // 2 + 1)])


if __name__ == '__main__':
    unittest.main()
