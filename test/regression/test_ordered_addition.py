import random
import unittest
from collections import Counter

from cplib.datastructure.avltree import AVLTree
from cplib.datastructure.binarytrie import BinaryTrie, MergeableBinaryTrie
from cplib.datastructure.fenwicktree import RangeMultisetBIT, RangeSetBIT, SortedMultisetBIT, SortedSetBIT
from cplib.datastructure.treap import Treap, TreapMultiset


class SetAdditionTest(unittest.TestCase):
    def test_addition_against_set(self) -> None:
        universe = [0, 3, 7, 15]
        for tree in (AVLTree[int](), Treap[int](), BinaryTrie(4), RangeSetBIT(16), SortedSetBIT(universe)):
            rng = random.Random(0)
            values: set[int] = set()
            for step in range(200):
                value = rng.choice(universe)
                with self.subTest(structure=type(tree).__name__, step=step):
                    if rng.randrange(3):
                        self.assertIs(tree.add(value), value not in values)
                        values.add(value)
                    else:
                        self.assertIs(tree.discard(value), value in values)
                        values.discard(value)
                    for query in range(-1, 18):
                        self.assertEqual(tree.bisect_left(query), sum(v < query for v in values))
                        self.assertEqual(tree.bisect_right(query), sum(v <= query for v in values))

    def test_mergeable_trie_addition_and_updates(self) -> None:
        for calc_reverse in (False, True):
            tree = MergeableBinaryTrie(4, lambda a, b: a + b, '', calc_reverse=calc_reverse)
            root = tree.new_trie()
            other_root = tree.new_trie()
            self.assertIs(tree.add(root, 5, 'b'), True)
            self.assertIs(tree.add(root, 1, 'a', update=True), True)
            self.assertIs(tree.add(root, 5, 'ignored'), False)
            self.assertEqual(tree.prod(root), ('ab', 'ba' if calc_reverse else ''))
            self.assertIs(tree.add(root, 5, 'c', update=True), False)
            self.assertEqual(tree.size(root), 2)
            self.assertEqual(tree.prod(root), ('ac', 'ca' if calc_reverse else ''))
            self.assertIs(tree.add(other_root, 5, 'd', update=True), True)
            self.assertEqual(tree.size(other_root), 1)
            self.assertIs(tree.discard(root, 5), True)
            self.assertIs(tree.add(root, 5, 'e'), True)
            self.assertEqual(tree.size(root), 2)
            self.assertEqual(tree.prod(root), ('ae', 'ea' if calc_reverse else ''))
            self.assertEqual(tree.prod(other_root), ('d', 'd' if calc_reverse else ''))


class MultisetAdditionTest(unittest.TestCase):
    def test_addition_against_counter(self) -> None:
        universe = [0, 3, 7, 15]
        for tree in (TreapMultiset[int](), RangeMultisetBIT(16), SortedMultisetBIT(universe)):
            rng = random.Random(0)
            values: Counter[int] = Counter()
            for step in range(200):
                value = rng.choice(universe)
                count = rng.randrange(-1, 6)
                with self.subTest(structure=type(tree).__name__, step=step):
                    if rng.randrange(3):
                        if count < 0:
                            with self.assertRaises(ValueError):
                                tree.add(value, count=count)
                        else:
                            result = tree.add(value, count=count)
                            self.assertIs(type(result), int)
                            self.assertEqual(result, count)
                            values[value] += count
                    else:
                        removed = min(max(count, 0), values[value])
                        self.assertEqual(tree.discard(value, count=max(count, 0)), removed)
                        values[value] -= removed
                    for query in universe:
                        self.assertEqual(tree.count(query), values[query])
                    for query in range(-1, 18):
                        self.assertEqual(tree.bisect_left(query), sum(c for v, c in values.items() if v < query))
                        self.assertEqual(tree.bisect_right(query), sum(c for v, c in values.items() if v <= query))

    def test_default_and_large_counts(self) -> None:
        for tree in (TreapMultiset[str](), SortedMultisetBIT(['cat', 'dog'])):
            self.assertEqual(tree.add('cat'), 1)
            self.assertEqual(tree.add('cat', 10**12), 10**12)
            self.assertEqual(tree.add('dog', count=2), 2)
            self.assertEqual(tree.count('cat'), 10**12 + 1)
            self.assertEqual(tree.bisect_left('dog'), 10**12 + 1)
            self.assertEqual(tree.bisect_right('dog'), 10**12 + 3)
        tree = RangeMultisetBIT(8)
        self.assertEqual(tree.add(3), 1)
        self.assertEqual(tree.add(3, 10**12), 10**12)
        self.assertEqual(tree.count(3), 10**12 + 1)

    def test_zero_and_negative_counts(self) -> None:
        for tree in (TreapMultiset[int](), RangeMultisetBIT(0), SortedMultisetBIT[int]([])):
            for value in (-1, 0, 1):
                result = tree.add(value, count=0)
                self.assertIs(type(result), int)
                self.assertEqual(result, 0)
                with self.assertRaises(ValueError):
                    tree.add(value, count=-1)
            self.assertEqual(tree.bisect_right(10), 0)
        for tree in (TreapMultiset[int](), RangeMultisetBIT(16), SortedMultisetBIT([5])):
            tree.add(5, 3)
            for value in (-1, 5, 16):
                self.assertEqual(tree.add(value, count=0), 0)
                with self.assertRaises(ValueError):
                    tree.add(value, count=-1)
                self.assertEqual(tree.count(5), 3)
                self.assertEqual(tree.bisect_right(100), 3)

    def test_invalid_addition_preserves_contents(self) -> None:
        ranged = RangeMultisetBIT(8)
        ranged.add(3, 2)
        for value in (-1, 8):
            with self.assertRaises(AssertionError):
                ranged.add(value, count=1)
        self.assertEqual(list(ranged), [3, 3])
        sorted_values = SortedMultisetBIT([3])
        sorted_values.add(3, 2)
        with self.assertRaises(KeyError):
            sorted_values.add(4, count=1)
        self.assertEqual(list(sorted_values), [3, 3])


if __name__ == '__main__':
    unittest.main()
