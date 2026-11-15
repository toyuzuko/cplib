"""Deterministic brute-force regressions for integer floor sums and XOR spans."""

import itertools
import random
import unittest

from cplib.mathematics import XorBasis, floor_sum


class FloorSumTests(unittest.TestCase):
    def test_exhaustive_signed(self):
        for n, m, a, b in itertools.product(range(10), range(1, 10), range(-12, 13), range(-12, 13)):
            self.assertEqual(floor_sum(n, m, a, b), sum((a * i + b) // m for i in range(n)), (n, m, a, b))

    def test_large_operands(self):
        rng = random.Random(641)
        for _ in range(300):
            n = rng.randrange(100)
            m = rng.randrange(1, 1 << 200)
            a = rng.randrange(-(1 << 250), 1 << 250)
            b = rng.randrange(-(1 << 250), 1 << 250)
            self.assertEqual(floor_sum(n, m, a, b), sum((a * i + b) // m for i in range(n)))
        n = 10 ** 100
        self.assertEqual(floor_sum(n, 1, -3, 7), -3 * n * (n - 1) // 2 + 7 * n)
        self.assertEqual(floor_sum(n, n, 1, 0), 0)
        self.assertEqual(floor_sum(n, n, -1, 0), 1 - n)

    def test_invalid(self):
        for args in [(-1, 2, 3, 4), (2, 0, 3, 4), (2, -1, 3, 4), (0, 0, 0, 0)]:
            with self.assertRaises(ValueError):
                floor_sum(*args)


class XorBasisTests(unittest.TestCase):
    def check_values(self, values):
        basis = XorBasis()
        span = {0}
        for value in values:
            self.assertEqual(basis.add(value), value not in span)
            span |= {x ^ value for x in span}
            self.assertEqual(1 << len(basis), len(span))
            for query in range(32):
                self.assertEqual(basis.contains(query), query in span)
                self.assertEqual(query in basis, query in span)
                self.assertEqual(basis.max_xor(query), max(x ^ query for x in span))
                self.assertEqual(basis.min_xor(query), min(x ^ query for x in span))
        self.assertEqual(XorBasis(iter(values)).max_xor(), max(span))

    def test_exhaustive_small(self):
        for values in itertools.product(range(8), repeat=3):
            self.check_values(values)

    def test_random_and_large(self):
        rng = random.Random(193)
        for _ in range(100):
            self.check_values([rng.randrange(32) for _ in range(10)])
        self.check_values([0, 1 << 1000, 1 << 500, (1 << 1000) ^ (1 << 500), 7, 7])

    def test_empty(self):
        basis = XorBasis()
        self.assertEqual(len(basis), 0)
        self.assertTrue(0 in basis)
        self.assertFalse(1 in basis)
        self.assertEqual(basis.min_xor(12), 12)
        self.assertEqual(basis.max_xor(12), 12)

    def test_negative(self):
        basis = XorBasis([3])
        for method in [basis.add, basis.contains, basis.min_xor, basis.max_xor]:
            with self.assertRaises(ValueError):
                method(-1)
        with self.assertRaises(ValueError):
            XorBasis([-1])
        self.assertEqual(len(basis), 1)


if __name__ == '__main__':
    unittest.main()
