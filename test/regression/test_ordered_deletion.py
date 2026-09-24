import random
import unittest
from collections import Counter
from functools import partial
from types import SimpleNamespace
from unittest.mock import patch

from cplib.datastructure.avltree import AVLTree
from cplib.datastructure.binarytrie import BinaryTrie, MergeableBinaryTrie
from cplib.datastructure.bst import BinarySearchTree
from cplib.datastructure.fenwicktree import FenwickTree, RangeMultisetBIT, RangeSetBIT, SortedMultisetBIT, SortedSetBIT
from cplib.datastructure.treap import Treap, TreapMultiset


class SetDeletionTest(unittest.TestCase):
    def test_guaranteed_updates(self) -> None:
        for cls in (AVLTree, Treap):
            tree = cls[int]()
            values = list(range(32))
            random.Random(0).shuffle(values)
            for value in values:
                self.assertIs(tree.add(value, validity_check=False), True)
            for remaining, value in enumerate(values):
                if cls is Treap:
                    self.assertIs(tree.discard(value, validity_check=False), True)
                else:
                    self.assertIs(tree.discard(value), True)
                self.assertEqual(tree.size(), 31 - remaining)
            self.assertIs(tree.discard(10), False)

    def test_deletion_against_set(self) -> None:
        universe = [0, 3, 7, 15]
        structures = []
        for cls in (AVLTree, Treap):
            tree = cls[int]()
            structures.append((cls.__name__, SimpleNamespace(
                add=tree.add, discard=tree.discard, remove=tree.remove,
                contents=lambda tree=tree: [tree.get(i) for i in range(tree.size())],
            )))
        for tree in (BinaryTrie(4), RangeSetBIT(16), SortedSetBIT(universe)):
            structures.append((type(tree).__name__, SimpleNamespace(
                add=tree.add, discard=tree.discard, remove=tree.remove,
                contents=lambda tree=tree: [tree[i] for i in range(len(tree))],
            )))
        bst = BinarySearchTree()
        structures.append(('BinarySearchTree', SimpleNamespace(
            add=bst.add, discard=bst.discard, remove=bst.remove, contents=bst.inorder,
        )))
        trie = MergeableBinaryTrie(4, lambda a, b: a + b, 0)
        root = trie.new_trie()
        structures.append(('MergeableBinaryTrie', SimpleNamespace(
            add=lambda value: trie.add(root, value, value),
            discard=partial(trie.discard, root), remove=partial(trie.remove, root),
            contents=lambda: [trie.get(root, i)[0] for i in range(trie.size(root))],
        )))
        for name, tree in structures:
            rng = random.Random(0)
            values: set[int] = set()
            for step in range(200):
                operation = rng.randrange(3)
                value = rng.choice(universe if operation == 0 else [-1, *universe, 5, 16])
                with self.subTest(structure=name, step=step):
                    if operation == 0:
                        tree.add(value)
                        values.add(value)
                    elif operation == 1:
                        self.assertIs(tree.discard(value), value in values)
                        values.discard(value)
                    elif value in values:
                        self.assertIsNone(tree.remove(value))
                        values.remove(value)
                    else:
                        with self.assertRaises(KeyError):
                            tree.remove(value)
                    self.assertEqual(tree.contents(), sorted(values))

    def test_mergeable_trie_roots_and_aggregates(self) -> None:
        tree = MergeableBinaryTrie(4, lambda a, b: a + b, '', calc_reverse=True)
        root = tree.new_trie()
        for key, value in ((1, 'a'), (5, 'b'), (9, 'c')):
            tree.add(root, key, value)
        self.assertIsNone(tree.remove(root, 5))
        self.assertEqual(tree.prod(root), ('ac', 'ca'))
        self.assertIs(tree.discard(root, 5), False)
        with self.assertRaises(KeyError):
            tree.remove(root, 5)
        self.assertEqual(tree.prod(root), ('ac', 'ca'))
        for invalid_root in (-1, 0, len(tree.cnt_type)):
            for method in (tree.discard, tree.remove):
                for value in (-1, 1, 16):
                    with self.assertRaises(ValueError):
                        method(invalid_root, value)
        self.assertEqual(tree.prod(root), ('ac', 'ca'))

    def test_trie_deletion_after_xor(self) -> None:
        tree = BinaryTrie(4)
        for value in (1, 3, 5):
            tree.add(value)
        tree.all_xor(7)
        self.assertIs(tree.discard(6), True)
        self.assertIsNone(tree.remove(4))
        self.assertEqual([tree[i] for i in range(len(tree))], [2])


class MultisetDeletionTest(unittest.TestCase):
    def test_guaranteed_removal(self) -> None:
        for tree in (TreapMultiset[int](), RangeMultisetBIT(16), SortedMultisetBIT([2, 5, 9])):
            for value in (2, 5, 9):
                for _ in range(5):
                    tree.add(value)
            for value in (5, 2, 9):
                self.assertIsNone(tree.remove(value, count=2, validity_check=False))
                self.assertEqual(tree.count(value), 3)
                self.assertIsNone(tree.remove(value, count=3, validity_check=False))
                self.assertEqual(tree.count(value), 0)
            self.assertEqual(tree.bisect_right(20), 0)
            self.assertIsNone(tree.remove(-100, count=0, validity_check=False))
            with self.assertRaises(ValueError):
                tree.remove(5, count=-1, validity_check=False)

    def test_guaranteed_removal_skips_availability_lookup(self) -> None:
        for validity_check in (True, False):
            tree = TreapMultiset[int]()
            tree.add(5, 3)
            calls = []
            original_find = TreapMultiset._find_

            def find(instance, key):
                calls.append(key)
                return original_find(instance, key)

            with patch.object(TreapMultiset, '_find_', find):
                tree.remove(5, count=1, validity_check=validity_check)
            self.assertEqual(len(calls), 2 if validity_check else 1)
            self.assertEqual(tree.count(5), 2)

            for tree in (RangeMultisetBIT(16), SortedMultisetBIT([5])):
                for _ in range(3):
                    tree.add(5)
                calls = []
                original_get = FenwickTree.get

                def get(instance, position):
                    calls.append(position)
                    return original_get(instance, position)

                with patch.object(FenwickTree, 'get', get):
                    tree.remove(5, count=1, validity_check=validity_check)
                self.assertEqual(len(calls), 1 if validity_check else 0)
                self.assertEqual(tree.count(5), 2)

    def test_deletion_against_counter(self) -> None:
        universe = [0, 3, 7, 15]
        for tree in (TreapMultiset[int](), RangeMultisetBIT(16), SortedMultisetBIT(universe)):
            rng = random.Random(0)
            values = Counter()
            for value in universe:
                for _ in range(8):
                    tree.add(value)
                    values[value] += 1
            for step in range(200):
                operation = rng.randrange(3)
                value = rng.choice(universe if operation == 0 else [-1, *universe, 5, 16])
                count = rng.randrange(-1, 5)
                with self.subTest(structure=type(tree).__name__, step=step):
                    if operation == 0:
                        tree.add(value)
                        values[value] += 1
                    else:
                        method = tree.discard if operation == 1 else tree.remove
                        if count < 0:
                            with self.assertRaises(ValueError):
                                method(value, count=count)
                        elif operation == 1:
                            removed = min(count, values[value])
                            result = method(value, count=count)
                            self.assertIs(type(result), int)
                            self.assertEqual(result, removed)
                            values[value] -= removed
                        elif values[value] < count:
                            with self.assertRaises(KeyError):
                                method(value, count=count)
                        else:
                            self.assertIsNone(method(value, count=count))
                            values[value] -= count
                    for query in universe:
                        self.assertEqual(tree.count(query), values[query])
                        self.assertEqual(tree.bisect_left(query), sum(c for v, c in values.items() if v < query))
                        self.assertEqual(tree.bisect_right(query), sum(c for v, c in values.items() if v <= query))

    def test_zero_and_negative_counts(self) -> None:
        for tree in (TreapMultiset[int](), RangeMultisetBIT(0), SortedMultisetBIT([])):
            for value in (-1, 0, 1):
                self.assertEqual(tree.discard(value, count=0), 0)
                self.assertIsNone(tree.remove(value, count=0))
                for method in (tree.discard, tree.remove):
                    with self.assertRaises(ValueError):
                        method(value, count=-1)

    def test_bulk_removal(self) -> None:
        for tree in (TreapMultiset[int](), RangeMultisetBIT(16), SortedMultisetBIT([5])):
            for _ in range(3):
                tree.add(5)
            with self.assertRaises(KeyError):
                tree.remove(5, count=4)
            self.assertEqual(tree.count(5), 3)
            self.assertEqual(tree.discard(5, count=4), 3)
            self.assertEqual(tree.count(5), 0)
            self.assertEqual(tree.discard(5), 0)


if __name__ == '__main__':
    unittest.main()
