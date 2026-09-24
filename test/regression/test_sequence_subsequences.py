import random
import unittest

from cplib.sequence.subseq import longest_increasing_subsequence, number_of_subsequences


class SequenceSubsequencesTest(unittest.TestCase):
    def test_lis_against_enumeration(self) -> None:
        rng = random.Random(0)
        cases = [[], [10**100], [-(10**100), 0, 10**100], [1 << 30] * 4]
        cases += [[rng.randrange(-4, 5) * 10**20 for _ in range(rng.randrange(10))] for _ in range(180)]
        for arr in cases:
            expected = 0
            for mask in range(1 << len(arr)):
                subsequence = [value for i, value in enumerate(arr) if mask >> i & 1]
                if all(a < b for a, b in zip(subsequence, subsequence[1:])):
                    expected = max(expected, len(subsequence))
            indices = longest_increasing_subsequence(arr, return_idx=True)
            values = longest_increasing_subsequence(arr)
            self.assertEqual(len(indices), expected)
            self.assertEqual(values, [arr[i] for i in indices])
            self.assertTrue(all(a < b for a, b in zip(indices, indices[1:])))
            self.assertTrue(all(a < b for a, b in zip(values, values[1:])))

    def test_distinct_subsequences_against_enumeration(self) -> None:
        rng = random.Random(0)
        for _ in range(180):
            arr = [rng.randrange(4) for _ in range(rng.randrange(11))]
            expected = len({tuple(value for i, value in enumerate(arr) if mask >> i & 1) for mask in range(1 << len(arr))})
            for mod in (1, 2, 7, 998244353):
                self.assertEqual(number_of_subsequences(arr, mod), expected % mod)
        self.assertEqual(number_of_subsequences([], 1), 0)
        for arr in ([], [1]):
            for mod in (0, -1):
                with self.assertRaises(ValueError):
                    number_of_subsequences(arr, mod)


if __name__ == '__main__':
    unittest.main()
