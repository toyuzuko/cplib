import random
import unittest

from cplib.datastructure.bst import BinarySearchTree


class BinarySearchTreeReuseTest(unittest.TestCase):
    def test_traversal_after_deletion_and_reinsertion(self) -> None:
        cases = [
            ([4], 4, 9, [9], [9]),
            ([4, 2, 6], 2, 5, [4, 6, 5], [5, 6, 4]),
            ([4, 2, 6, 5], 6, 7, [4, 2, 5, 7], [2, 7, 5, 4]),
            ([4, 2, 6, 1, 3, 7], 4, 8, [6, 2, 1, 3, 7, 8], [1, 3, 2, 8, 7, 6]),
            ([4, 2, 6, 1, 3, 5, 7], 4, 8, [5, 2, 1, 3, 6, 7, 8], [1, 3, 2, 8, 7, 6, 5]),
            ([10, 4, 20, 15, 25, 12, 17, 13], 10, 11, [12, 4, 11, 20, 15, 13, 17, 25], [11, 4, 13, 17, 15, 25, 20, 12]),
        ]
        for initial, removed, added, preorder, postorder in cases:
            with self.subTest(initial=initial, removed=removed):
                tree = BinarySearchTree[int]()
                for value in initial:
                    tree.add(value)
                self.assertTrue(tree.discard(removed))
                self.assertFalse(tree.discard(removed))
                self.assertTrue(tree.add(added))
                self.assertFalse(tree.add(added))
                self.assertEqual(tree.preorder(), preorder)
                self.assertEqual(tree.postorder(), postorder)
                self.assertEqual(tree.inorder(), sorted(preorder))
                self.assertEqual(tree.size(), len(preorder))
                for value in preorder:
                    self.assertTrue(tree.contains(value))

    def test_repeated_clear_and_refill(self) -> None:
        rng = random.Random(0)
        tree = BinarySearchTree[int]()
        for _ in range(50):
            keys = list(range(32))
            rng.shuffle(keys)
            fresh = BinarySearchTree[int]()
            for value in keys:
                tree.add(value)
                fresh.add(value)
            self.assertEqual(tree.inorder(), fresh.inorder())
            self.assertEqual(tree.preorder(), fresh.preorder())
            self.assertEqual(tree.postorder(), fresh.postorder())
            rng.shuffle(keys)
            for value in keys:
                tree.remove(value)
            self.assertEqual(tree.size(), 0)
            self.assertEqual(tree.inorder(), [])
            self.assertEqual(tree.preorder(), [])
            self.assertEqual(tree.postorder(), [])

    def test_reused_slots_on_skewed_trees(self) -> None:
        for order in (range(1000), range(999, -1, -1)):
            tree = BinarySearchTree[int]()
            for value in order:
                tree.add(value)
            for value in order:
                tree.remove(value)
            for value in order:
                tree.add(value)
            self.assertEqual(tree.inorder(), list(range(1000)))
            self.assertEqual(tree.preorder(), list(order))
            self.assertEqual(tree.postorder(), list(reversed(order)))


if __name__ == '__main__':
    unittest.main()
