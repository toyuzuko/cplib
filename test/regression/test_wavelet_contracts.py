import random
import unittest

from cplib.datastructure.wavelet import FullyIndexableDictionary, WaveletMatrix


class WaveletContractTests(unittest.TestCase):
    def test_bit_vector_boundaries_and_rebuild(self):
        rng = random.Random(0)
        for n in [0, 1, 2, 31, 32, 33, 63, 64, 65, 96, 127, 128, 129]:
            actual = FullyIndexableDictionary(n)
            bits = [0] * n
            for _ in range(3):
                for i in range(n):
                    if rng.randrange(4) == 0:
                        bits[i] = 1
                        actual.set(i)
                actual.build()
                for i, bit in enumerate(bits):
                    self.assertEqual(actual.access(i), bit)
                for v in [0, 1]:
                    for r in range(n + 1):
                        self.assertEqual(actual.rank(r, v), bits[:r].count(v))
                    positions = [i for i, bit in enumerate(bits) if bit == v]
                    for k in range(-2, len(positions) + 2):
                        self.assertEqual(actual.select(k, v), positions[k] if 0 <= k < len(positions) else -1)
            for k in [-1, n, n + 1]:
                for method in [actual.set, actual.access]:
                    with self.assertRaises(AssertionError):
                        method(k)
            for k in [-1, n + 1]:
                with self.assertRaises(AssertionError):
                    actual.rank(k, 0)
            for v in [-1, 2]:
                with self.assertRaises(AssertionError):
                    actual.rank(0, v)
                with self.assertRaises(AssertionError):
                    actual.select(-1, v)
        with self.assertRaises(ValueError):
            FullyIndexableDictionary(-1)

    def test_matrix_queries(self):
        rng = random.Random(1)
        for log in [0, 1, 2, 5, 65]:
            actual = WaveletMatrix(log)
            limit = 1 << log
            self.assertEqual(actual.rank(0, 0), 0)
            self.assertEqual(actual.select(0, 0), -1)
            self.assertEqual(actual.range_freq_lt(0, 0, 1), 0)
            self.assertEqual(actual.range_sum_lt(0, 0, 1), 0)
            for n in [0, 1, 2, 9, 31, 32, 33, 64]:
                values = [rng.randrange(limit) for _ in range(n)]
                actual.build(values)
                self.assertEqual([actual.access(i) for i in range(n)], values)
                queries = sorted(set([-1, 0, limit - 1, limit, limit + 1] + values))
                for x in queries:
                    positions = [i for i, value in enumerate(values) if value == x]
                    for k in range(-1, len(positions) + 2):
                        self.assertEqual(actual.select(x, k), positions[k] if 0 <= k < len(positions) else -1)
                    for r in range(n + 1):
                        self.assertEqual(actual.rank(x, r), values[:r].count(x))
                ranges = [(l, r) for l in range(n + 1) for r in range(l, n + 1)] if n <= 9 else [(0, n), (n, n)] + [tuple(sorted((rng.randrange(n + 1), rng.randrange(n + 1)))) for _ in range(100)]
                for l, r in ranges:
                    part = values[l:r]
                    for x in rng.sample(queries, min(8, len(queries))):
                        self.assertEqual(actual.range_freq(l, r, x), part.count(x))
                        less = [v for v in part if v < x]
                        self.assertEqual(actual.range_freq_lt(l, r, x), len(less))
                        self.assertEqual(actual.range_sum_lt(l, r, x), sum(less))
                    ordered = sorted(part)
                    for k in range(len(ordered)):
                        self.assertEqual(actual.quantile(l, r, k), ordered[k])
                for bad in [-1, limit]:
                    with self.assertRaises(ValueError):
                        actual.build([0, bad])
                    self.assertEqual([actual.access(i) for i in range(n)], values)
                if values:
                    values[0] = -1
                    self.assertGreaterEqual(actual.access(0), 0)
        with self.assertRaises(ValueError):
            WaveletMatrix(-1)

    def test_invalid_ranges(self):
        for log in [0, 3]:
            actual = WaveletMatrix(log)
            actual.build([0, 0, 0])
            for k in [-1, 3, 100]:
                with self.assertRaises(AssertionError):
                    actual.access(k)
            for r in [-1, 4]:
                with self.assertRaises(AssertionError):
                    actual.rank(-100, r)
            for l, r in [(-1, 2), (0, 4), (2, 1), (4, 4)]:
                for method in [actual.range_freq, actual.range_freq_lt, actual.range_sum_lt, actual.quantile]:
                    with self.assertRaises(AssertionError):
                        method(l, r, 0)
            for l, r, k in [(0, 0, 0), (0, 3, -1), (1, 3, 2)]:
                with self.assertRaises(AssertionError):
                    actual.quantile(l, r, k)


if __name__ == '__main__':
    unittest.main()
