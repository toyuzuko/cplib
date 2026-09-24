from fractions import Fraction
from functools import lru_cache
from itertools import combinations, permutations, product
from math import comb
import random
import unittest

from cplib.mathematics.combinatorics import (
    TwelvefoldWay, count_all_subset_sums, count_four_sum,
    count_subset_sums_with_size_in_range, enumerate_bell_number,
    enumerate_bernoulli_number, enumerate_montmort_number,
    enumerate_partition_number, enumerate_stirling_number_first,
    enumerate_stirling_number_second,
)
from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod


@lru_cache(None)
def distributions(balls: bool, boxes: bool, restriction: str, n: int, k: int) -> int:
    seen: set[object] = set()
    for assignment in product(range(k), repeat=n):
        groups = tuple(tuple(i for i, box in enumerate(assignment) if box == j) for j in range(k))
        counts = tuple(map(len, groups))
        if restriction == 'at_most_one' and any(c > 1 for c in counts):
            continue
        if restriction == 'at_least_one' and any(c == 0 for c in counts):
            continue
        key = groups if balls else counts
        seen.add(key if boxes else tuple(sorted(key)))
    return len(seen)


class CombinatoricsContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = FormalPowerSeriesMod.get_mod()
        self.transform = ConvolutionMod.get_mod()

    def tearDown(self) -> None:
        if FormalPowerSeriesMod.get_mod() != self.modulus:
            FormalPowerSeriesMod.set_mod(self.modulus)
        if ConvolutionMod.get_mod() != self.transform:
            ConvolutionMod.set_mod(self.transform)

    def test_twelvefold_distributions(self) -> None:
        for balls, boxes, restriction in product((False, True), (False, True), ('any', 'at_most_one', 'at_least_one')):
            counter = TwelvefoldWay(balls, boxes, restriction)
            for modulus in (1, 2, 4, 6, 7, 15, 25, 1000000007):
                counter.mod = modulus
                for n in range(6):
                    for k in range(5):
                        self.assertEqual(counter.count(n, k), distributions(balls, boxes, restriction, n, k) % modulus, (balls, boxes, restriction, modulus, n, k))
                self.assertEqual(counter.count(-1, 3), 0)
                self.assertEqual(counter.count(3, -1), 0)
        for modulus in (0, -1):
            with self.assertRaises(ValueError):
                TwelvefoldWay(True, True, mod=modulus)
        with self.assertRaises(ValueError):
            TwelvefoldWay(True, True, 'invalid')
        counter = TwelvefoldWay(False, True)
        self.assertEqual(counter.count(3, 10**20), comb(10**20 + 2, 3) % counter.mod)
        self.assertEqual(TwelvefoldWay(False, False).count(3, 10**20), 3)
        self.assertEqual(TwelvefoldWay(True, True, 'at_least_one').count(3, 10**20), 0)
        counter.mod = 0
        with self.assertRaises(ValueError):
            counter.count(3, 4)
        counter.mod = 8
        self.assertEqual(counter.count(3, 4), 20 % 8)

    def test_stirling_and_bell(self) -> None:
        size = 30
        first = [[0] * (size + 1) for _ in range(size + 1)]
        second = [[0] * (size + 1) for _ in range(size + 1)]
        first[0][0] = second[0][0] = 1
        for n in range(1, size + 1):
            for k in range(1, n + 1):
                first[n][k] = first[n - 1][k - 1] - (n - 1) * first[n - 1][k]
                second[n][k] = second[n - 1][k - 1] + k * second[n - 1][k]
        for modulus in (2, 3, 17, 97, 257, 998244353, 1000000007):
            FormalPowerSeriesMod.set_mod(modulus)
            for n in (0, 1, 2, 5, 15, size):
                self.assertEqual(enumerate_bell_number(n), [sum(second[i]) % modulus for i in range(n + 1)])
                for method, table in ((enumerate_stirling_number_first, first), (enumerate_stirling_number_second, second)):
                    self.assertEqual(method(n, None), [x % modulus for x in table[n][:n + 1]])
                    for k in list(range(n + 2)) + [-1]:
                        expected = [table[i][k] % modulus for i in range(n + 1)] if 0 <= k <= n else [0] * (n + 1)
                        self.assertEqual(method(n, k), expected, (method.__name__, modulus, n, k))
            for method in (enumerate_stirling_number_first, enumerate_stirling_number_second):
                with self.assertRaises(ValueError):
                    method(-1, None)
        # Another helper may have changed the shared transform modulus.
        FormalPowerSeriesMod.set_mod(998244353)
        ConvolutionMod.set_mod(17)
        self.assertEqual(enumerate_bell_number(5), [1, 1, 2, 5, 15, 52])

    def test_partitions_and_bernoulli(self) -> None:
        for modulus in (2, 17, 97, 998244353, 1000000007):
            FormalPowerSeriesMod.set_mod(modulus)
            for n in (0, 1, 10, 50, 100):
                expected = [1] + [0] * n
                for part in range(1, n + 1):
                    for total in range(part, n + 1):
                        expected[total] += expected[total - part]
                self.assertEqual(enumerate_partition_number(n), [x % modulus for x in expected])
            n = min(20, modulus - 2)
            bernoulli = [Fraction(1)]
            for i in range(1, n + 1):
                bernoulli.append(-sum(comb(i + 1, j) * bernoulli[j] for j in range(i)) / (i + 1))
            expected = [x.numerator * pow(x.denominator, -1, modulus) % modulus for x in bernoulli]
            self.assertEqual(enumerate_bernoulli_number(n), expected)
            if modulus < 100:
                with self.assertRaises(ValueError):
                    enumerate_bernoulli_number(modulus - 1)
        for method in (enumerate_partition_number, enumerate_bernoulli_number, enumerate_bell_number):
            with self.assertRaises(ValueError):
                method(-1)

    def test_subset_enumeration(self) -> None:
        rng = random.Random(0)
        for modulus in (2, 17, 97, 998244353, 1000000007):
            FormalPowerSeriesMod.set_mod(modulus)
            for _ in range(100):
                values = [rng.randrange(12) for _ in range(rng.randrange(10))]
                target = rng.randrange(20)
                expected = [0] * (target + 1)
                for mask in range(1 << len(values)):
                    value = sum(x for i, x in enumerate(values) if mask >> i & 1)
                    if value <= target:
                        expected[value] += 1
                self.assertEqual(count_all_subset_sums(values, target), [x % modulus for x in expected])
            self.assertEqual(count_all_subset_sums([0, 0, 100], 0), [4 % modulus])
            self.assertEqual(count_all_subset_sums([], 0), [1])
        for values, target in (([-1], 3), ([1], -1)):
            with self.assertRaises(ValueError):
                count_all_subset_sums(values, target)
        for _ in range(300):
            values = [rng.randrange(-10, 11) for _ in range(rng.randrange(11))]
            size = rng.randrange(-1, len(values) + 2)
            lower, upper = rng.randrange(-20, 21), rng.randrange(-20, 21)
            expected = sum(lower <= sum(xs) <= upper for xs in combinations(values, size)) if 0 <= size <= len(values) else 0
            self.assertEqual(count_subset_sums_with_size_in_range(values, size, lower, upper), expected)
            arrays = [[rng.randrange(-3, 4) for _ in range(rng.randrange(5))] for _ in range(4)]
            target = rng.randrange(-10, 11)
            self.assertEqual(count_four_sum(*arrays, target), sum(sum(xs) == target for xs in product(*arrays)))

    def test_montmort(self) -> None:
        expected = [sum(all(i != x for i, x in enumerate(p)) for p in permutations(range(n))) for n in range(8)]
        for modulus in (1, 2, 6, 17, 998244353):
            for n in range(8):
                self.assertEqual(enumerate_montmort_number(n, modulus), [x % modulus for x in expected[:n + 1]])
        for n, modulus in ((-1, 2), (1, 0), (1, -1)):
            with self.assertRaises(ValueError):
                enumerate_montmort_number(n, modulus)


if __name__ == '__main__':
    unittest.main()
