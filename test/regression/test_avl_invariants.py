import random
import unittest
from bisect import bisect_left, bisect_right

from cplib.datastructure.avltree import AVLTree


class OrderedKey:
    def __init__(self, value: int) -> None:
        self.value = value

    def __lt__(self, other: 'OrderedKey') -> bool:
        return self.value < other.value


class AVLInvariantsTest(unittest.TestCase):
    def test_balance_counts_rebuild_and_reuse(self) -> None:
        rng = random.Random(0)
        tree = AVLTree[int]()
        values: set[int] = set()
        peak = 0
        for step in range(5000):
            key = rng.randrange(-100, 101)
            action = rng.randrange(5)
            if action == 0 and step % 31 == 0:
                initial = [rng.randrange(-100, 101) for _ in range(rng.randrange(100))]
                ordered = bool(step % 2)
                tree.build(sorted(initial) if ordered else initial, ordered)
                values = set(initial)
                peak = len(values)
            elif action <= 2:
                self.assertEqual(tree.add(key), key not in values)
                values.add(key)
            else:
                self.assertEqual(tree.discard(key), key in values)
                values.discard(key)
            peak = max(peak, len(values))
            expected = sorted(values)
            self.assertEqual(list(tree), expected)
            self.assertEqual(tree.size(), len(values))
            self.assertEqual(tree.contains(key), key in values)
            self.assertEqual(tree.bisect_left(key), bisect_left(expected, key))
            self.assertEqual(tree.bisect_right(key), bisect_right(expected, key))
            self.assertEqual(tree.successor(key), next((v for v in expected if v >= key), None))
            self.assertEqual(tree.predecessor(key, False), next((v for v in reversed(expected) if v < key), None))
            if key in values:
                self.assertEqual(tree.index(key), expected.index(key))
            else:
                with self.assertRaises(ValueError):
                    tree.index(key)
            if values:
                i = rng.randrange(len(values))
                self.assertEqual(tree.get(i), expected[i])
            seen: set[int] = set()
            stack = [tree.root]
            while stack:
                node = stack.pop()
                if not node:
                    continue
                self.assertNotIn(node, seen)
                seen.add(node)
                l, r = tree.left[node], tree.right[node]
                self.assertLessEqual(abs(tree.height[l] - tree.height[r]), 1)
                self.assertEqual(tree.height[node], max(tree.height[l], tree.height[r]) + 1)
                self.assertEqual(tree.cnt[node], tree.cnt[l] + tree.cnt[r] + 1)
                stack.extend((l, r))
            self.assertEqual(len(seen), len(values))
            self.assertEqual(len(tree.key), peak + (peak > 0))
            self.assertFalse(seen.intersection(tree.free_nodes))
        tree.build([])
        self.assertEqual(list(tree), [])
        for index in (-1, 0, 1):
            with self.assertRaises(IndexError):
                tree.get(index)
        tree.add(3, validity_check=False)
        self.assertEqual(tree.get(0), 3)
        for index in (-1, 1, 2):
            with self.assertRaises(IndexError):
                tree.get(index)

    def test_only_less_than_keys(self) -> None:
        tree = AVLTree[OrderedKey]()
        tree.build([OrderedKey(4), OrderedKey(1), OrderedKey(4)])
        self.assertEqual([v.value for v in tree], [1, 4])
        self.assertFalse(tree.add(OrderedKey(4)))
        self.assertTrue(tree.contains(OrderedKey(4)))
        self.assertEqual(tree.index(OrderedKey(4)), 1)
        self.assertTrue(tree.discard(OrderedKey(4)))
        self.assertEqual([v.value for v in tree], [1])


if __name__ == '__main__':
    unittest.main()
