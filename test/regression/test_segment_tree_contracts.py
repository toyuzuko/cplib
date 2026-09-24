import random
import unittest
from bisect import bisect_right

from cplib.datastructure.segtree import (
    SegmentTree, LazySegmentTree, DualSegmentTree, SegmentTree2D,
    SegmentTreeBeats, RangeLinearAddRangeMin, MergeSortTree, RangeAffineRangeSum,
)


class SegmentTreeContractsTest(unittest.TestCase):
    def test_rebuild_and_noncommutative_search(self) -> None:
        identity = (0, 1, 2)

        def mapping(f: tuple[int, ...], value: str) -> str:
            return ''.join('abc'[f[ord(c) - ord('a')]] for c in value)

        def composition(f: tuple[int, ...], g: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(f[g[i]] for i in range(3))

        for n in (0, 1, 2, 7, 16, 25):
            rng = random.Random(n)
            plain = SegmentTree(n, str.__add__, '')
            lazy = LazySegmentTree(n, str.__add__, '', mapping, composition, identity)
            values = [''] * n
            for step in range(300):
                l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                if step % 13 == 0:
                    prefix = [rng.choice('abc') for _ in range(rng.randrange(n + 1))]
                    values = prefix + [''] * (n - len(prefix))
                    plain.build(prefix)
                    lazy.build(values)
                elif step % 3 == 0:
                    f = tuple(rng.sample(range(3), 3))
                    lazy.range_apply(l, r, f)
                    for i in range(l, r):
                        values[i] = mapping(f, values[i])
                        plain.set(i, values[i])
                elif n:
                    i = rng.randrange(n)
                    values[i] = rng.choice('abc')
                    plain.set(i, values[i])
                    lazy.set(i, values[i])
                limit = rng.randrange(n + 1)
                predicate = lambda s: len(s) <= limit and 'ab' not in s
                right = l
                while right < n and predicate(''.join(values[l:right + 1])):
                    right += 1
                left = r
                while left and predicate(''.join(values[left - 1:r])):
                    left -= 1
                for tree in (plain, lazy):
                    self.assertEqual(tree.prod(l, r), ''.join(values[l:r]))
                    self.assertEqual(tree.all_prod(), ''.join(values))
                    self.assertEqual(tree.max_right(l, predicate), right)
                    self.assertEqual(tree.min_left(r, predicate), left)
                    if n:
                        self.assertEqual(tree.get(l % n), values[l % n])
            for tree in (plain, lazy):
                with self.assertRaises(AssertionError):
                    tree.build(['x'] * (n + 1))
                self.assertEqual(tree.all_prod(), ''.join(values))

    def test_dual_chronology_and_rebuild(self) -> None:
        for n in (0, 1, 2, 7, 16):
            rng = random.Random(n)
            tree = DualSegmentTree(n, str.__add__, '')
            values = [''] * n
            for step in range(300):
                l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                value = rng.choice('abc')
                if step % 17 == 0:
                    values = [rng.choice('abc') for _ in range(n)]
                    tree.build(values)
                elif step % 5 == 0:
                    tree.all_apply(value)
                    values = [value + v for v in values]
                else:
                    tree.range_apply(l, r, value)
                    values[l:r] = [value + v for v in values[l:r]]
                if n:
                    i = rng.randrange(n)
                    self.assertEqual(tree.get(i), values[i])
                if step % 11 == 0:
                    self.assertEqual(tree.get_all(), values)
            self.assertEqual(tree.get_all(), values)
            for flag in (False, True):
                tree = DualSegmentTree(n, int.__add__, 0, commutative=flag)
                tree.all_apply(3)
                tree.range_apply(0, n, 7)
                self.assertEqual(tree.get_all(), [10] * n)
                tree.build([2] * n)
                self.assertEqual(tree.get_all(), [2] * n)

    def test_dense_two_dimensional_tree(self) -> None:
        for n, m in ((0, 0), (0, 3), (3, 0), (1, 1), (1, 5), (5, 1), (3, 5), (8, 8)):
            rng = random.Random(n * 10 + m)
            tree = SegmentTree2D(n, m, int.__add__, 0)
            values = [[0] * m for _ in range(n)]
            for step in range(220):
                if step % 17 == 0:
                    values = [[rng.randrange(-100, 101) for _ in range(m)] for _ in range(n)]
                    tree.build(values)
                elif n and m:
                    i, j = rng.randrange(n), rng.randrange(m)
                    value = rng.randrange(-100, 101)
                    tree.set(i, j, value)
                    values[i][j] = value
                    self.assertEqual(tree.get(i, j), value)
                l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                u, d = sorted((rng.randrange(m + 1), rng.randrange(m + 1)))
                self.assertEqual(tree.prod(l, r, u, d), sum(sum(row[u:d]) for row in values[l:r]))
                self.assertEqual(tree.all_prod(), sum(map(sum, values)))
                if n:
                    i = rng.randrange(n)
                    self.assertEqual(tree.prod_single_row(i, u, d), sum(values[i][u:d]))
            with self.assertRaises(AssertionError):
                tree.prod_single_row(n, 0, m)
            with self.assertRaises(AssertionError):
                tree.build(values + [[0] * m])
            self.assertEqual(tree.all_prod(), sum(map(sum, values)))

    def test_beats_arbitrary_integers_and_rebuild(self) -> None:
        huge = 1 << 100
        pool = [0, 1, -1, 1 << 60, -(1 << 60), huge, -huge, huge + 1]
        for n in (0, 1, 2, 7, 16, 25):
            rng = random.Random(n)
            tree = SegmentTreeBeats(n)
            values = [0] * n
            for step in range(650):
                l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                value = rng.choice(pool)
                action = rng.randrange(6)
                if action == 0:
                    prefix = [rng.choice(pool) for _ in range(rng.randrange(n + 1))]
                    tree.build(prefix)
                    values = prefix + [0] * (n - len(prefix))
                elif action == 1:
                    tree.range_add(l, r, value)
                    values[l:r] = [v + value for v in values[l:r]]
                elif action == 2:
                    tree.range_set(l, r, value)
                    values[l:r] = [value] * (r - l)
                elif action == 3:
                    tree.range_chmin(l, r, value)
                    values[l:r] = [min(v, value) for v in values[l:r]]
                elif action == 4:
                    tree.range_chmax(l, r, value)
                    values[l:r] = [max(v, value) for v in values[l:r]]
                elif n:
                    i = rng.randrange(n)
                    tree.set(i, value)
                    values[i] = value
                self.assertEqual(tree.range_sum(l, r), sum(values[l:r]))
                self.assertEqual(tree.range_min(l, r), min(values[l:r], default=tree.pinf))
                self.assertEqual(tree.range_max(l, r), max(values[l:r], default=tree.ninf))
                self.assertEqual(tree.all_sum(), sum(values))
                self.assertEqual(tree.all_min(), min(values, default=tree.pinf))
                self.assertEqual(tree.all_max(), max(values, default=tree.ninf))
                if n:
                    i = rng.randrange(n)
                    self.assertEqual(tree.get(i), values[i])
            for method in (tree.range_add, tree.range_set, tree.range_chmin, tree.range_chmax):
                with self.assertRaises(AssertionError):
                    method(0, n + 1, 3)
            with self.assertRaises(AssertionError):
                tree.build([0] * (n + 1))
            self.assertEqual([tree.get(i) for i in range(n)], values)

    def test_linear_add_large_minima(self) -> None:
        huge = 1 << 100
        for n in (0, 1, 2, 7, 31):
            for block in (1, 3, 10):
                rng = random.Random(n)
                values = [huge + rng.randrange(10) for _ in range(n)]
                tree = RangeLinearAddRangeMin(values, block)
                for _ in range(200):
                    l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                    self.assertEqual(tree.range_min(l, r), min(values[l:r], default=tree.inf))
                    b, c = rng.randrange(-20, 20), rng.choice((-huge, 0, huge))
                    tree.range_linear_add(l, r, b, c)
                    for i in range(l, r):
                        values[i] += b * i + c
                    if n:
                        i = rng.randrange(n)
                        self.assertEqual(tree.get(i), values[i])
        for values in ([], [1]):
            for block in (0, -1):
                with self.assertRaises(ValueError):
                    RangeLinearAddRangeMin(values, block)

    def test_merge_sort_rebuild(self) -> None:
        for n in (0, 1, 2, 7, 16):
            rng = random.Random(n)
            tree = MergeSortTree(n, int.__add__, 0)
            self.assertEqual(tree.prod_le(0, n, 100), (0, 0))
            for _ in range(200):
                values = [rng.randrange(-10, 11) for _ in range(n)]
                tree.build(values)
                l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                bound = rng.randrange(-12, 13)
                selected = sorted(values[l:r])
                count = bisect_right(selected, bound)
                self.assertEqual(tree.prod_le(l, r, bound), (count, sum(selected[:count])))
            with self.assertRaises(AssertionError):
                tree.build(values + [0])
            with self.assertRaises(AssertionError):
                tree.prod_le(-1, n, 0)

    def test_affine_wrapper(self) -> None:
        for n in (0, 1, 2, 7):
            for mod in (1, 7, 998244353):
                rng = random.Random(n)
                tree = RangeAffineRangeSum(n, lambda: mod)
                values = [0] * n
                tree.range_affine(0, n, 0, 3 % mod)
                values = [3 % mod] * n
                self.assertEqual(tree.range_sum(0, n), sum(values) % mod)
                for step in range(200):
                    l, r = sorted((rng.randrange(n + 1), rng.randrange(n + 1)))
                    if step % 17 == 0:
                        initial = [rng.randrange(-10**15, 10**15) for _ in range(n)]
                        values = [v % mod for v in initial]
                        tree.build(initial)
                    else:
                        a, b = rng.randrange(mod), rng.randrange(mod)
                        tree.range_affine(l, r, a, b)
                        values[l:r] = [(a * v + b) % mod for v in values[l:r]]
                    self.assertEqual(tree.range_sum(l, r), sum(values[l:r]) % mod)

        for mod in (0, -1, 1 << 30):
            with self.assertRaises(AssertionError):
                RangeAffineRangeSum(1, lambda: mod)

    def test_negative_capacities(self) -> None:
        constructors = (
            lambda: SegmentTree(-1, int.__add__, 0),
            lambda: LazySegmentTree(-1, int.__add__, 0, int.__mul__, int.__mul__, 1),
            lambda: DualSegmentTree(-1, int.__add__, 0),
            lambda: SegmentTree2D(-1, 1, int.__add__, 0),
            lambda: SegmentTree2D(1, -1, int.__add__, 0),
            lambda: SegmentTreeBeats(-1),
            lambda: MergeSortTree(-1, int.__add__, 0),
            lambda: RangeAffineRangeSum(-1, lambda: 7),
        )
        for create in constructors:
            with self.assertRaises(ValueError):
                create()


if __name__ == '__main__':
    unittest.main()
