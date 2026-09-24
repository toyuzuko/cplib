import bisect
import random
import unittest
from functools import partial
from types import SimpleNamespace

from cplib.datastructure.avltree import AVLTree
from cplib.datastructure.binarytrie import BinaryTrie, MergeableBinaryTrie
from cplib.datastructure.fenwicktree import RangeMultisetBIT, RangeSetBIT, SortedMultisetBIT, SortedSetBIT
from cplib.datastructure.treap import Treap, TreapMultiset


class OrderedSearchTest(unittest.TestCase):
    def check_search(self, tree, values, queries) -> None:
        for query in queries:
            left = bisect.bisect_left(values, query)
            right = bisect.bisect_right(values, query)
            self.assertEqual(tree.bisect_left(query), left)
            self.assertEqual(tree.bisect_right(query), right)
            if left != right:
                self.assertEqual(tree.index(query), left)
            else:
                with self.assertRaises(ValueError):
                    tree.index(query)

    def test_search_after_updates(self) -> None:
        universe = [0, 3, 7, 12, 15]
        merged = MergeableBinaryTrie(4, lambda a, b: a + b, 0)
        root = merged.new_trie()
        adapter = SimpleNamespace(
            add=lambda value: merged.add(root, value, value),
            discard=partial(merged.discard, root),
            index=partial(merged.index, root),
            bisect_left=partial(merged.bisect_left, root),
            bisect_right=partial(merged.bisect_right, root),
        )
        structures = [
            ('AVLTree', AVLTree[int](), False),
            ('Treap', Treap[int](), False),
            ('TreapMultiset', TreapMultiset[int](), True),
            ('BinaryTrie', BinaryTrie(4), False),
            ('MergeableBinaryTrie', adapter, False),
            ('RangeSetBIT', RangeSetBIT(16), False),
            ('RangeMultisetBIT', RangeMultisetBIT(16), True),
            ('SortedSetBIT', SortedSetBIT(universe), False),
            ('SortedMultisetBIT', SortedMultisetBIT(universe), True),
        ]
        for name, tree, multiset in structures:
            rng = random.Random(0)
            values: list[int] = []
            for step in range(151):
                if step:
                    value = rng.choice(universe)
                    if rng.randrange(2):
                        tree.add(value)
                        if multiset or value not in values:
                            bisect.insort(values, value)
                    else:
                        tree.discard(value)
                        if value in values:
                            values.remove(value)
                with self.subTest(structure=name, step=step):
                    self.check_search(tree, values, [-10**30, *range(-1, 18), 10**30])

    def test_search_with_string_keys(self) -> None:
        for tree in (AVLTree[str](), Treap[str](), TreapMultiset[str](), SortedSetBIT(['!', 'cat', 'dog']), SortedMultisetBIT(['!', 'cat', 'dog'])):
            for value in ('!', 'dog'):
                tree.add(value)
            with self.subTest(structure=type(tree).__name__):
                self.check_search(tree, ['!', 'dog'], ['', '!', 'cat', 'dog', 'zebra'])

    def test_search_after_build(self) -> None:
        for cls in (AVLTree, Treap, TreapMultiset):
            for is_sorted in (False, True):
                tree = cls[int]()
                values = [9, 5, 2, -1, 5]
                if is_sorted:
                    values.sort()
                tree.build(values, is_sorted=is_sorted)
                expected = sorted(values if cls is TreapMultiset else set(values))
                with self.subTest(structure=cls.__name__, is_sorted=is_sorted):
                    self.check_search(tree, expected, range(-2, 11))
                    tree.build([], is_sorted=is_sorted)
                    self.check_search(tree, [], range(-2, 11))
                    tree.add(5)
                    self.check_search(tree, [5], range(-2, 11))
                    tree.build([2, 2, 9], is_sorted=is_sorted)
                    self.check_search(tree, [2, 2, 9] if cls is TreapMultiset else [2, 9], range(-2, 11))

    def test_zero_capacity(self) -> None:
        for tree in (RangeSetBIT(0), RangeMultisetBIT(0), SortedSetBIT([]), SortedMultisetBIT([])):
            with self.subTest(structure=type(tree).__name__):
                self.check_search(tree, [], [-1, 0, 1])

    def test_trie_search_after_xor(self) -> None:
        tree = BinaryTrie(4)
        values = [0, 3, 7, 15]
        for value in values:
            tree.add(value)
        for mask in range(16):
            tree.all_xor(mask)
            values = sorted(value ^ mask for value in values)
            self.check_search(tree, values, range(-2, 19))

    def test_mergeable_trie_split_and_merge(self) -> None:
        tree = MergeableBinaryTrie(4, lambda a, b: a + b, 0)
        root = tree.new_trie()
        for value in (1, 5, 7):
            tree.add(root, value, value)
        left, right = tree.safe_split(root, 4)
        for root, values in ((left, [1]), (right, [5, 7])):
            adapter = SimpleNamespace(**{name: partial(getattr(tree, name), root) for name in ('bisect_left', 'bisect_right', 'index')})
            self.check_search(adapter, values, range(-1, 18))
        root = tree.merge(left, right)
        self.assertEqual(tree.bisect_right(root, 5), 2)
        self.assertEqual(tree.index(root, 7), 2)
        for method in (tree.bisect_left, tree.bisect_right, tree.index):
            for query in (-1, 3, 16):
                with self.assertRaises(ValueError):
                    method(0, query)


class SortedBITNeighborTest(unittest.TestCase):
    def test_query_between_registered_values(self) -> None:
        for cls in (SortedSetBIT, SortedMultisetBIT):
            with self.subTest(structure=cls.__name__):
                tree = cls([2, 5, 9])
                for value in (2, 5, 9):
                    tree.add(value)
                self.assertEqual(tree.predecessor(4), 2)
                self.assertEqual(tree.successor(4, False), 5)
                self.assertEqual(tree.predecessor(10), 9)

    def test_neighbors_against_sorted_list(self) -> None:
        universe = [2, 5, 9, 14]
        for cls in (SortedSetBIT, SortedMultisetBIT):
            rng = random.Random(0)
            tree = cls(universe)
            values: list[int] = []
            for step in range(101):
                if step:
                    value = rng.choice(universe)
                    if rng.randrange(2):
                        tree.add(value)
                        if cls is SortedMultisetBIT or value not in values:
                            bisect.insort(values, value)
                    else:
                        tree.discard(value)
                        if value in values:
                            values.remove(value)
                for query in range(-1, 17):
                    left = bisect.bisect_left(values, query)
                    right = bisect.bisect_right(values, query)
                    for method, same, index in (
                        (tree.predecessor, True, right - 1),
                        (tree.predecessor, False, left - 1),
                        (tree.successor, True, left),
                        (tree.successor, False, right),
                    ):
                        with self.subTest(structure=cls.__name__, step=step, query=query, method=method.__name__, same=same):
                            if 0 <= index < len(values):
                                self.assertEqual(method(query, same), values[index])
                            else:
                                self.assertIsNone(method(query, same))


if __name__ == '__main__':
    unittest.main()
