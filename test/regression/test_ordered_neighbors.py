from __future__ import annotations

import bisect
import random
import unittest
from collections.abc import Callable, Iterable
from functools import partial
from typing import assert_type

from cplib.datastructure.avltree import AVLTree
from cplib.datastructure.binarytrie import BinaryTrie, MergeableBinaryTrie
from cplib.datastructure.fenwicktree import RangeMultisetBIT, RangeSetBIT, SortedMultisetBIT, SortedSetBIT
from cplib.datastructure.treap import Treap, TreapMultiset


class OrderedKey:
    def __init__(self, rank: int) -> None:
        self.rank = rank

    def __lt__(self, other: OrderedKey) -> bool:
        return self.rank < other.rank


class OrderedNeighborTest(unittest.TestCase):
    def check_neighbors(self, successor: Callable[[int, bool], int | None], predecessor: Callable[[int, bool], int | None], values: list[int], queries: Iterable[int]) -> None:
        for query in queries:
            left = bisect.bisect_left(values, query)
            right = bisect.bisect_right(values, query)
            for method, inclusive, index in (
                (successor, True, left), (successor, False, right),
                (predecessor, True, right - 1), (predecessor, False, left - 1),
            ):
                expected = values[index] if 0 <= index < len(values) else None
                self.assertEqual(method(query, inclusive), expected)

    def test_neighbors_after_updates(self) -> None:
        universe = [0, 3, 7, 12, 15]
        trees = (
            AVLTree[int](), Treap[int](), TreapMultiset[int](), BinaryTrie(4),
            RangeSetBIT(16), RangeMultisetBIT(16), SortedSetBIT(universe), SortedMultisetBIT(universe),
        )
        for tree in trees:
            rng = random.Random(0)
            values: list[int] = []
            multiset = isinstance(tree, (TreapMultiset, RangeMultisetBIT, SortedMultisetBIT))
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
                with self.subTest(structure=type(tree).__name__, step=step):
                    self.check_neighbors(tree.successor, tree.predecessor, values, [-10**30, *range(-1, 18), 10**30])
                    self.assertEqual(tree.successor(0), tree.successor(0, inclusive=True))
                    self.assertEqual(tree.predecessor(0), tree.predecessor(0, inclusive=True))
                    self.assertEqual(tree.successor(0, False), tree.successor(0, inclusive=False))
                    self.assertEqual(tree.predecessor(0, False), tree.predecessor(0, inclusive=False))

    def test_zero_capacity_and_empty_trees(self) -> None:
        for tree in (RangeSetBIT(0), RangeMultisetBIT(0), SortedSetBIT[int]([]), SortedMultisetBIT[int]([])):
            self.check_neighbors(tree.successor, tree.predecessor, [], [-1, 0, 1])

    def test_stored_sentinel_and_type_narrowing(self) -> None:
        for tree in (AVLTree[int](), Treap[int](), TreapMultiset[int]()):
            for value in (-1, 0, 2):
                tree.add(value)
            self.check_neighbors(tree.successor, tree.predecessor, [-1, 0, 2], range(-2, 4))
            result = tree.successor(-2)
            assert_type(result, int | None)
            self.assertEqual(result, -1)
            assert result is not None
            assert_type(result, int)
            self.assertEqual(result + 1, 0)
        for tree in (AVLTree[str](), Treap[str](), TreapMultiset[str](), SortedSetBIT(['', 'cat', 'dog']), SortedMultisetBIT(['', 'cat', 'dog'])):
            tree.add('')
            tree.add('dog')
            self.assertEqual(tree.predecessor('cat'), '')
            self.assertEqual(tree.successor(''), '')
            self.assertEqual(tree.successor('', inclusive=False), 'dog')
            self.assertIsNone(tree.predecessor('', inclusive=False))
            self.assertIsNone(tree.successor('zebra'))
            result = tree.successor('cat')
            assert_type(result, str | None)
            if result is not None:
                assert_type(result, str)
                self.assertEqual(result.upper(), 'DOG')

    def test_order_equivalence_without_equality(self) -> None:
        keys = [OrderedKey(rank) for rank in (1, 3, 5)]
        for tree in (AVLTree[OrderedKey](), Treap[OrderedKey](), TreapMultiset[OrderedKey](), SortedSetBIT(keys), SortedMultisetBIT(keys)):
            for key in keys:
                tree.add(key)
            for query_rank in range(7):
                query = OrderedKey(query_rank)
                for inclusive in (True, False):
                    greater = [key for key in keys if key.rank >= query_rank] if inclusive else [key for key in keys if key.rank > query_rank]
                    lesser = [key for key in keys if key.rank <= query_rank] if inclusive else [key for key in keys if key.rank < query_rank]
                    with self.subTest(structure=type(tree).__name__, query=query_rank, inclusive=inclusive):
                        self.assertIs(tree.successor(query, inclusive=inclusive), greater[0] if greater else None)
                        self.assertIs(tree.predecessor(query, inclusive=inclusive), lesser[-1] if lesser else None)

    def test_trie_after_xor_and_deletions(self) -> None:
        for bitlen in (0, 1, 4):
            tree = BinaryTrie(bitlen)
            values = list(range(1 << bitlen))
            for value in values:
                tree.add(value)
            for mask in range(1 << bitlen):
                tree.all_xor(mask)
                values = sorted(value ^ mask for value in values)
                if values:
                    tree.discard(values.pop(0))
                with self.subTest(bitlen=bitlen, mask=mask):
                    self.check_neighbors(tree.successor, tree.predecessor, values, range(-1, (1 << bitlen) + 1))

    def test_mergeable_trie_updates_split_and_merge(self) -> None:
        tree = MergeableBinaryTrie(4, lambda a, b: a + b, 0)
        root = tree.new_trie()
        rng = random.Random(0)
        values: list[int] = []
        for step in range(151):
            if step:
                value = rng.randrange(16)
                if rng.randrange(2):
                    tree.add(root, value, 100 + value, update=True)
                    if value not in values:
                        bisect.insort(values, value)
                else:
                    tree.discard(root, value)
                    if value in values:
                        values.remove(value)
            with self.subTest(step=step):
                self.check_neighbors(partial(tree.successor, root), partial(tree.predecessor, root), values, [-10**30, *range(-1, 18), 10**30])
                self.assertEqual(tree.prod(root)[0], sum(100 + v for v in values))
                split = rng.randrange(17)
                left, right = tree.safe_split(root, split)
                for part, expected in ((left, [v for v in values if v < split]), (right, [v for v in values if v >= split])):
                    self.check_neighbors(partial(tree.successor, part), partial(tree.predecessor, part), expected, range(-1, 18))
                root = tree.merge(left, right)

    def test_mergeable_trie_invalid_roots(self) -> None:
        tree = MergeableBinaryTrie(2, lambda a, b: a + b, 0)
        root = tree.new_trie()
        tree.add(root, 1, 10)
        child = tree.ptr[root * 3]
        for invalid_root in (-10**30, -1, 0, child, len(tree.cnt_type), 10**30):
            for method in (tree.successor, tree.predecessor):
                for value in (-1, 1, 4):
                    for inclusive in (True, False):
                        with self.assertRaises(ValueError):
                            method(invalid_root, value, inclusive=inclusive)
        self.assertEqual(tree.successor(root, 0), 1)
        self.assertEqual(tree.predecessor(root, 2), 1)
        self.assertIsNone(tree.successor(root, 1, inclusive=False))
        self.assertIsNone(tree.predecessor(root, 1, inclusive=False))
        self.assertEqual(tree.prod(root)[0], 10)


if __name__ == '__main__':
    unittest.main()
