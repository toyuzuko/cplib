import bisect
import random
import unittest

from cplib.datastructure.fenwicktree import FenwickTree, GroupFenwickTree, GroupRangeAddPointGet, RangeAddPointGet, RangeMultisetBIT, RangeSetBIT, SortedMultisetBIT, SortedSetBIT


class OrderedKey:
    def __init__(self, value: int) -> None:
        self.value = value

    def __lt__(self, other: 'OrderedKey') -> bool:
        return self.value < other.value


class FenwickRebuildTest(unittest.TestCase):
    def test_prefix_and_group_rebuilds(self) -> None:
        rng = random.Random(0)
        for n in range(25):
            tree = FenwickTree(n)
            group = GroupFenwickTree(n, lambda a, b: a ^ b, lambda a: a, 0)
            values = [0] * n
            xor_values = [0] * n
            for _ in range(100):
                action = rng.randrange(3)
                if not n or action == 0:
                    initial = [rng.randrange(10) for _ in range(rng.randrange(n + 1))]
                    tree.build(initial)
                    group.build(initial)
                    values = initial + [0] * (n - len(initial))
                    xor_values = values[:]
                else:
                    p, value = rng.randrange(n), rng.randrange(10)
                    if action == 1:
                        tree.add(p, value)
                        group.add(p, value)
                        values[p] += value
                        xor_values[p] ^= value
                    else:
                        tree.set(p, value)
                        group.set(p, value)
                        values[p] = xor_values[p] = value
                self.assertEqual([tree.get(i) for i in range(n)], values)
                self.assertEqual([group.get(i) for i in range(n)], xor_values)
                l, r = sorted([rng.randrange(n + 1), rng.randrange(n + 1)])
                expected = 0
                for v in xor_values[l:r]:
                    expected ^= v
                self.assertEqual(group.prod(l, r), expected)
                self.assertEqual(tree.range_sum(l, r), sum(values[l:r]))
                target = rng.randrange(-1, sum(values) + 3)
                prefixes = [sum(values[:i]) for i in range(n + 1)]
                self.assertEqual(tree.bisect_left(target), bisect.bisect_left(prefixes, target))
            before = tree.data[:]
            with self.assertRaises(AssertionError):
                tree.build([1] * (n + 1))
            self.assertEqual(tree.data, before)

    def test_range_updates_and_short_builds(self) -> None:
        rng = random.Random(0)
        for n in range(20):
            tree = RangeAddPointGet(n)
            group = GroupRangeAddPointGet(n, lambda a, b: a ^ b, lambda a: a, 0)
            values = [0] * n
            xor_values = [0] * n
            for _ in range(100):
                if rng.randrange(3) == 0:
                    initial = [rng.randrange(10) for _ in range(rng.randrange(n + 1))]
                    tree.build(initial)
                    group.build(initial)
                    values = initial + [0] * (n - len(initial))
                    xor_values = values[:]
                else:
                    l, r = sorted([rng.randrange(n + 1), rng.randrange(n + 1)])
                    value = rng.randrange(10)
                    tree.range_add(l, r, value)
                    group.range_add(l, r, value)
                    for i in range(l, r):
                        values[i] += value
                        xor_values[i] ^= value
                self.assertEqual([tree.get(i) for i in range(n)], values)
                self.assertEqual([group.get(i) for i in range(n)], xor_values)
            for ds in (tree, group):
                old = ds.bit.data[:]
                for l, r in ((-1, n), (0, n + 1), (1, 0)):
                    with self.assertRaises(AssertionError):
                        ds.range_add(l, r, 100)
                    self.assertEqual(ds.bit.data, old)
                for i in (-1, n):
                    with self.assertRaises(AssertionError):
                        ds.get(i)
                with self.assertRaises(AssertionError):
                    ds.build([1] * (n + 1))
                self.assertEqual(ds.bit.data, old)
                ds.build([])
                self.assertEqual([ds.get(i) for i in range(n)], [0] * n)

    def test_set_and_multiset_boundaries_and_counts(self) -> None:
        rng = random.Random(0)
        for n in (0, 1, 10, 25):
            for multiset in (False, True):
                tree = RangeMultisetBIT(n) if multiset else RangeSetBIT(n)
                for _ in range(100):
                    counts = [rng.randrange(4 if multiset else 2) for _ in range(n)]
                    if multiset:
                        tree.build(counts)
                    else:
                        tree.build([bool(v) for v in counts])
                    values = [i for i in range(n) for _ in range(counts[i])]
                    self.assertEqual(list(tree), values)
                    for i in (-2, -1, len(values), len(values) + 1):
                        with self.assertRaises(IndexError):
                            tree[i]
                        with self.assertRaises(IndexError):
                            tree.pop(i)
                        self.assertEqual(list(tree), values)
                    for value in range(-2, n + 3):
                        self.assertEqual(value in tree, value in values)
                        self.assertEqual(tree.bisect_left(value), bisect.bisect_left(values, value))
                        self.assertEqual(tree.bisect_right(value), bisect.bisect_right(values, value))
                        if multiset:
                            self.assertEqual(tree.count(value), values.count(value))
                    if values:
                        i = rng.randrange(len(values))
                        self.assertEqual(tree.pop(i), values.pop(i))
                        self.assertEqual(list(tree), values)
                    else:
                        with self.assertRaises(IndexError):
                            tree.min()
                        with self.assertRaises(IndexError):
                            tree.max()
        for tree in (RangeMultisetBIT(3), SortedMultisetBIT([0, 1, 2])):
            tree.build([1, 2, 3])
            with self.assertRaises(ValueError):
                tree.build([1, -1, 3])
            self.assertEqual(list(tree), [0, 1, 1, 2, 2, 2])

    def test_ordering_equivalence_and_candidate_ownership(self) -> None:
        for cls in (SortedSetBIT, SortedMultisetBIT):
            candidates = [OrderedKey(1), OrderedKey(3), OrderedKey(5)]
            tree = cls(candidates)
            candidates.clear()
            for value in (1, 3, 5):
                tree.add(OrderedKey(value))
                self.assertIn(OrderedKey(value), tree)
            self.assertEqual([key.value for key in tree], [1, 3, 5])
            for i, value in enumerate((1, 3, 5)):
                self.assertEqual(tree.index(OrderedKey(value)), i)
                self.assertEqual(tree.bisect_left(OrderedKey(value)), i)
                self.assertEqual(tree.bisect_right(OrderedKey(value)), i + 1)
            tree.remove(OrderedKey(3))
            self.assertNotIn(OrderedKey(3), tree)
            self.assertEqual([key.value for key in tree], [1, 5])

    def test_negative_capacities(self) -> None:
        factories = (FenwickTree, RangeAddPointGet, RangeSetBIT, RangeMultisetBIT,
                     lambda n: GroupFenwickTree(n, int.__add__, int.__neg__, 0),
                     lambda n: GroupRangeAddPointGet(n, int.__add__, int.__neg__, 0))
        for factory in factories:
            with self.assertRaises(ValueError):
                factory(-1)


if __name__ == '__main__':
    unittest.main()
