import bisect
import random
import unittest
from typing import assert_type

from cplib.datastructure.treap import Treap, TreapMultiset


class TreapConstructionTest(unittest.TestCase):
    def test_empty_first_insert_and_reinsert(self) -> None:
        for tree in (Treap[int](), TreapMultiset[int]()):
            self.assertEqual(tree.size(), 0)
            self.assertEqual(list(tree.iter()), [])
            self.assertEqual(list(tree.iter_range(-1, 1)), [])
            self.assertEqual(tree.bisect_left(0), 0)
            self.assertEqual(tree.bisect_right(0), 0)
            self.assertFalse(tree.contains(0))
            self.assertFalse(tree.discard(0))
            self.assertIsNone(tree.successor(0))
            self.assertIsNone(tree.predecessor(0))
            with self.assertRaises(KeyError):
                tree.remove(0)
            for index in (-1, 0, 1):
                with self.assertRaises(IndexError):
                    tree.get(index)
            for value in (0, -1, 10**30):
                tree.add(value)
                self.assertEqual(tree.get(0), value)
                self.assertEqual(list(tree.iter()), [value])
                tree.remove(value)
                with self.assertRaises(IndexError):
                    tree.get(0)

    def test_build_clear_and_append(self) -> None:
        cases: list[list[str]] = [[], ['dog', '', 'cat', 'dog'], [], ['zebra'], []]
        for tree in (Treap[str](), TreapMultiset[str]()):
            multiset = isinstance(tree, TreapMultiset)
            for is_sorted in (False, True):
                for keys in cases:
                    source = sorted(keys) if is_sorted else keys[:]
                    tree.build(source, is_sorted=is_sorted)
                    expected = sorted(keys if multiset else set(keys))
                    self.assertEqual([tree.get(i) for i in range(tree.size())], expected)
                    self.assertEqual(source, sorted(keys) if is_sorted else keys)
                    tree.add('mouse')
                    bisect.insort(expected, 'mouse')
                    self.assertEqual([tree.get(i) for i in range(tree.size())], expected)
                    value = tree.get(0)
                    assert_type(value, str)
                    self.assertEqual(value.upper(), expected[0].upper())
                    for index in (-1, tree.size(), tree.size() + 1):
                        with self.assertRaises(IndexError):
                            tree.get(index)

    def test_noop_before_first_multiset_insert(self) -> None:
        tree = TreapMultiset[int]()
        self.assertEqual(tree.add(2, count=0), 0)
        with self.assertRaises(ValueError):
            tree.add(2, count=-1)
        self.assertEqual(tree.add(5, count=3), 3)
        self.assertEqual([tree.get(i) for i in range(tree.size())], [5, 5, 5])
        tree.remove(5, count=3, validity_check=False)
        tree.build([])
        self.assertEqual(tree.add(8, count=2), 2)
        self.assertEqual([tree.get(i) for i in range(tree.size())], [8, 8])

    def test_rank_access_after_random_updates_and_rebuilds(self) -> None:
        for tree in (Treap[int](), TreapMultiset[int]()):
            rng = random.Random(0)
            values: list[int] = []
            multiset = isinstance(tree, TreapMultiset)
            for step in range(300):
                operation = rng.randrange(4)
                value = rng.randrange(-10, 11)
                if operation == 0:
                    tree.add(value)
                    if multiset or value not in values:
                        bisect.insort(values, value)
                elif operation == 1:
                    tree.discard(value)
                    if value in values:
                        values.remove(value)
                else:
                    keys = [rng.randrange(-10, 11) for _ in range(rng.randrange(15))]
                    if operation == 3:
                        keys.sort()
                    tree.build(keys, is_sorted=operation == 3)
                    values = sorted(keys if multiset else set(keys))
                with self.subTest(structure=type(tree).__name__, step=step):
                    self.assertEqual(tree.size(), len(values))
                    self.assertEqual([tree.get(i) for i in range(tree.size())], values)
                    for index in (-1, len(values), len(values) + 1):
                        with self.assertRaises(IndexError):
                            tree.get(index)


if __name__ == '__main__':
    unittest.main()
