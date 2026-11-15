import random
import unittest
from fractions import Fraction

from cplib.algorithm import min_plus_convolution_convex_convex, subset_sum_bitset
from cplib.sequence import longest_common_subsequence_length, longest_common_subsequence_length_bitset


class BitparallelDPContractsTest(unittest.TestCase):
    def test_subset_sum_random(self) -> None:
        rng = random.Random(771)
        for _ in range(600):
            values = [rng.randrange(20) for _ in range(rng.randrange(15))]
            limit = rng.randrange(100)
            reachable = {0}
            for value in values:
                reachable |= {s + value for s in reachable if s + value <= limit}
            self.assertEqual(subset_sum_bitset(values, limit), sum(1 << s for s in reachable))

    def test_subset_sum_boundaries(self) -> None:
        self.assertEqual(subset_sum_bitset([], 10**30), 1)
        self.assertEqual(subset_sum_bitset([0, 0], 0), 1)
        self.assertEqual(subset_sum_bitset([10**30, 2, 2], 4), 21)
        self.assertEqual(subset_sum_bitset([2], 4), 5)  # not unbounded knapsack
        for values, limit in (([], -1), ([100, -1], 0), ([-2], 1)):
            with self.assertRaises(ValueError):
                subset_sum_bitset(values, limit)

    def test_lcs_random(self) -> None:
        rng = random.Random(772)
        for alphabet in (1, 3, 30, 10**9):
            for _ in range(160):
                a = [rng.randrange(alphabet) for _ in range(rng.randrange(50))]
                b = [rng.randrange(alphabet) for _ in range(rng.randrange(50))]
                expected = longest_common_subsequence_length(a, b)
                self.assertEqual(longest_common_subsequence_length_bitset(a, b), expected)
                self.assertEqual(longest_common_subsequence_length_bitset(b, a), expected)

    def test_lcs_domains(self) -> None:
        for a, b in (('', 'abc'), ('🍊ゆずこ🍊', 'ゆ🍊ずこ'), ('a' * 400, 'a' * 500)):
            self.assertEqual(longest_common_subsequence_length_bitset(a, b), longest_common_subsequence_length(a, b))
        self.assertEqual(longest_common_subsequence_length_bitset(b'abcde', b'ace'), 3)
        self.assertEqual(longest_common_subsequence_length_bitset([(1, 2), (3, 4)], [(3, 4)]), 1)
        # Existing equality-only API still supports unhashable elements.
        self.assertEqual(longest_common_subsequence_length([[1], [2]], [[2]]), 1)
        self.assertEqual(longest_common_subsequence_length_bitset(list(range(1000)), list(range(999, -1, -1))), 1)

    def test_convex_random(self) -> None:
        rng = random.Random(773)
        for _ in range(700):
            sequences: list[list[int]] = []
            for _ in range(2):
                values = [rng.randrange(-20, 21)] if rng.randrange(5) else []
                if values:
                    for slope in sorted(rng.randrange(-15, 16) for _ in range(rng.randrange(20))):
                        values.append(values[-1] + slope)
                sequences.append(values)
            a, b = sequences
            expected = [min(a[i] + b[k-i] for i in range(len(a)) if 0 <= k-i < len(b))
                        for k in range(len(a) + len(b) - 1)] if a and b else []
            self.assertEqual(min_plus_convolution_convex_convex(a, b), expected)

    def test_convex_boundaries(self) -> None:
        self.assertEqual(min_plus_convolution_convex_convex([10**100], [-10**100]), [0])
        self.assertEqual(min_plus_convolution_convex_convex([0, 0, 0], [0, 0]), [0] * 4)
        a = [Fraction(1, 3), Fraction(1, 4), Fraction(2, 3)]
        b = [Fraction(0), Fraction(1, 2)]
        self.assertEqual(min_plus_convolution_convex_convex(a, b),
                         [Fraction(1, 3), Fraction(1, 4), Fraction(2, 3), Fraction(7, 6)])
        for a, b in (([0, 2, 1], []), ([], [0, 2, 1]), ([0], [0, 1, 1])):
            with self.assertRaises(ValueError):
                min_plus_convolution_convex_convex(a, b)


if __name__ == '__main__':
    unittest.main()
