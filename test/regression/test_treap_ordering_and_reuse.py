import random
import unittest

from cplib.datastructure.treap import Treap, TreapMultiset


class OrderedKey:
    def __init__(self, value: int) -> None:
        self.value = value

    def __lt__(self, other: 'OrderedKey') -> bool:
        return self.value < other.value


class TreapOrderingAndReuseTest(unittest.TestCase):
    def test_order_equivalent_keys(self) -> None:
        for cls in (Treap, TreapMultiset):
            tree = cls()
            multiset = cls is TreapMultiset
            for mode in ('add', 'build'):
                values = [3, 1, 3, 2, 1, 3]
                tree.build([])
                if mode == 'build':
                    tree.build([OrderedKey(v) for v in values])
                else:
                    for v in values:
                        tree.add(OrderedKey(v))
                expected = sorted(values if multiset else set(values))
                self.assertEqual([k.value for k in tree.iter()], expected)
                for value in range(5):
                    self.assertEqual(tree.contains(OrderedKey(value)), value in expected)
                    self.assertEqual(tree.bisect_left(OrderedKey(value)), sum(v < value for v in expected))
                    if value in expected:
                        self.assertEqual(tree.index(OrderedKey(value)), expected.index(value))
                if multiset:
                    self.assertEqual(tree.count(OrderedKey(3)), 3)
                    self.assertEqual([(key.value, count) for key, count in tree.items()], [(1, 2), (2, 1), (3, 3)])
                for value in expected:
                    tree.remove(OrderedKey(value))
                self.assertEqual(tree.size(), 0)

    def test_maximum_priority_and_deep_iteration(self) -> None:
        for cls in (Treap, TreapMultiset):
            tree = cls()
            tree.rand = iter([(1 << 32) - 1] * 8)
            for v in (3, 1, 2):
                tree.add(v)
            self.assertEqual(list(tree.iter()), [1, 2, 3])
            for v in (1, 2, 3):
                tree.remove(v)
            tree.add(9)
            self.assertEqual(list(tree.iter()), [9])
            # Identical priorities deliberately form a chain; traversals must not recurse.
            n = 3000
            tree.rand = iter([5] * n)
            tree.build(list(range(n)), is_sorted=True)
            self.assertEqual(list(tree.iter()), list(range(n)))
            if cls is TreapMultiset:
                self.assertEqual(list(tree.items()), [(i, 1) for i in range(n)])
            tree.rand = iter([5] * n)
            for v in range(n):
                tree.remove(v)
            self.assertEqual(tree.size(), 0)

    def test_reuse_random_updates_and_rebuild(self) -> None:
        for cls in (Treap, TreapMultiset):
            rng = random.Random(0)
            tree = cls()
            counts: dict[int, int] = {}
            peak = 0
            for step in range(3000):
                value = rng.randrange(20)
                if step % 103 == 0:
                    tree.build([])
                    counts.clear()
                    peak = 0
                elif rng.randrange(2):
                    if cls is Treap:
                        added = value not in counts
                        self.assertEqual(tree.add(value), added)
                        counts[value] = 1
                    else:
                        count = rng.randrange(1, 5)
                        tree.add(value, count)
                        counts[value] = counts.get(value, 0) + count
                else:
                    if cls is Treap:
                        self.assertEqual(tree.discard(value), value in counts)
                        counts.pop(value, None)
                    else:
                        count = rng.randrange(1, 5)
                        removed = min(count, counts.get(value, 0))
                        self.assertEqual(tree.discard(value, count), removed)
                        if removed:
                            counts[value] -= removed
                            if counts[value] == 0:
                                del counts[value]
                peak = max(peak, len(counts))
                expected = [v for v in sorted(counts) for _ in range(counts[v])]
                self.assertEqual(list(tree.iter()), expected)
                self.assertEqual(tree.size(), len(expected))
                self.assertLessEqual(len(tree.key), peak + 1)
                self.assertEqual([tree.get(i) for i in range(tree.size())], expected)
                if cls is TreapMultiset:
                    self.assertEqual(tree.distinct_size(), len(counts))
            tree.build([])
            for i in range(2000):
                tree.add(i)
                tree.remove(i)
            self.assertEqual(len(tree.key), 2)


if __name__ == '__main__':
    unittest.main()
