import random
import unittest

from cplib.datastructure.sparsetable import SparseTable, DisjointSparseTable


class SparseTableContractsTest(unittest.TestCase):
    def test_input_ownership_and_ranges(self) -> None:
        rng = random.Random(0)
        for n in range(36):
            values = [rng.randrange(-100, 101) for _ in range(n)]
            for cls in (SparseTable, DisjointSparseTable):
                original = values[:]
                tree = cls(original, min)
                original[:] = [1000] * n
                for l in range(n):
                    for r in range(l + 1, n + 1):
                        self.assertEqual(tree.prod(l, r), min(values[l:r]))
                for l, r in ((-1, 0), (0, 0), (0, n + 1), (n, n), (n + 1, n), (-1, n)):
                    with self.assertRaises(AssertionError):
                        tree.prod(l, r)
                if n:
                    self.assertEqual(tree.prod(0, n), min(values))

    def test_noncommutative_semigroups(self) -> None:
        for n in range(1, 35):
            values = [(i, -i) for i in range(n)]
            tree = SparseTable(tuple(values), lambda a, b: (a[0], b[1]))
            text = [chr(65 + i % 26) for i in range(n)]
            disjoint = DisjointSparseTable(tuple(text), str.__add__)
            for l in range(n):
                for r in range(l + 1, n + 1):
                    self.assertEqual(tree.prod(l, r), (values[l][0], values[r - 1][1]))
                    self.assertEqual(disjoint.prod(l, r), ''.join(text[l:r]))


if __name__ == '__main__':
    unittest.main()
