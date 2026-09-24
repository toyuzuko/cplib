import random
import unittest
from collections.abc import Iterator
from operator import add, neg, sub

from cplib.graph.linkcut import BidirectionalLinkCutTree, DynamicTreeAddTreeSum, LazyPathLinkCutTree, LazySubtreeLinkCutTree, LinkCutTree


def trees(n: int) -> Iterator[LinkCutTree[int] | BidirectionalLinkCutTree[int] | LazyPathLinkCutTree[int, int] | LazySubtreeLinkCutTree[int, int] | DynamicTreeAddTreeSum]:
    yield LinkCutTree(n, 0, add)
    yield BidirectionalLinkCutTree(n, 0, add)
    yield LazyPathLinkCutTree(n, 0, add, lambda f, x, size: x + f * size, add, 0)
    yield LazySubtreeLinkCutTree(n, 0, add, neg, lambda f, x, size: x + f * size, add, sub, 0)
    yield DynamicTreeAddTreeSum(n)


class LinkCutNavigationTest(unittest.TestCase):
    def test_get_and_same_in_isolated_and_relinked_trees(self) -> None:
        for tree in trees(4):
            with self.subTest(tree=type(tree).__name__):
                tree.build([1, 2, 3, 4])
                self.assertTrue(tree.same(0, 0))
                self.assertFalse(tree.same(0, 1))
                tree.link(1, 0)
                tree.link(2, 1)
                tree.reroot(2)
                tree.set(1, 20)
                self.assertEqual(tree.get(1), 20)
                self.assertTrue(tree.same(0, 2))
                self.assertTrue(tree.same(2, 0))
                self.assertFalse(tree.same(0, 3))
                self.assertEqual(tree.root(0), 2)
                tree.cut_parent(1)
                self.assertTrue(tree.same(0, 1))
                self.assertFalse(tree.same(0, 2))
                tree.link(1, 3)
                self.assertTrue(tree.same(0, 3))
                self.assertFalse(tree.same(2, 3))
                self.assertEqual([tree.get(v) for v in range(4)], [1, 20, 3, 4])
                self.assertEqual([tree.root(v) for v in range(4)], [3, 3, 2, 3])

    def test_parent_after_reversing_a_chain(self) -> None:
        for tree in trees(7):
            with self.subTest(tree=type(tree).__name__):
                tree.build(list(range(7)))
                for v in range(1, 7):
                    tree.link(v, v - 1)
                tree.reroot(3)
                self.assertEqual(tree.parent(4), 3)
                tree.reroot(1)
                self.assertEqual(tree.parent(0), 1)
                tree.reroot(6)
                self.assertEqual(tree.parent(1), 2)
                self.assertEqual([tree.root(v) for v in range(7)], [6] * 7)
                self.assertEqual([tree.parent(v) for v in range(7)], [1, 2, 3, 4, 5, 6, -1])

    def test_random_navigation_and_updates(self) -> None:
        for seed in range(10):
            for tree in trees(16):
                rng = random.Random(seed)
                n = 16
                values = [rng.randrange(-20, 21) for _ in range(n)]
                parent = [-1] + [rng.randrange(v) for v in range(1, n)]
                tree.build(values[:])
                for v in range(1, n):
                    tree.link(v, parent[v])

                def root(v: int) -> int:
                    while parent[v] != -1:
                        v = parent[v]
                    return v

                def reroot(v: int) -> None:
                    previous = -1
                    while v != -1:
                        next_vertex = parent[v]
                        parent[v] = previous
                        previous, v = v, next_vertex

                def subtree(v: int) -> list[int]:
                    nodes = [v]
                    for u in nodes:
                        nodes.extend(w for w in range(n) if parent[w] == u)
                    return nodes

                for step in range(400):
                    v = rng.randrange(n)
                    value = rng.randrange(-10, 11)
                    op = rng.randrange(7)
                    with self.subTest(tree=type(tree).__name__, seed=seed, step=step, op=op):
                        if op == 0:
                            tree.reroot(v)
                            reroot(v)
                        elif op == 1:
                            if parent[v] != -1:
                                tree.cut_parent(v)
                                parent[v] = -1
                        elif op == 2:
                            u = rng.randrange(n)
                            if root(u) != root(v):
                                child = root(v)
                                tree.link(child, u)
                                parent[child] = u
                        elif op == 3:
                            tree.set(v, value)
                            values[v] = value
                        elif isinstance(tree, (LinkCutTree, BidirectionalLinkCutTree, LazyPathLinkCutTree)):
                            u = rng.choice(subtree(root(v)))
                            reroot(u)
                            path = [v]
                            while parent[path[-1]] != -1:
                                path.append(parent[path[-1]])
                            if op == 4 and isinstance(tree, LazyPathLinkCutTree):
                                tree.path_apply(u, v, value)
                                for w in path:
                                    values[w] += value
                            else:
                                expected = sum(values[w] for w in path)
                                actual = tree.path_prod(u, v)
                                self.assertEqual(actual, (expected, expected) if isinstance(tree, BidirectionalLinkCutTree) else expected)
                        else:
                            nodes = subtree(v)
                            if op == 4:
                                if isinstance(tree, DynamicTreeAddTreeSum):
                                    tree.subtree_add(v, value)
                                else:
                                    tree.subtree_apply(v, value)
                                for w in nodes:
                                    values[w] += value
                            elif op == 5:
                                actual = tree.subtree_sum(v) if isinstance(tree, DynamicTreeAddTreeSum) else tree.subtree_aggregate(v)
                                self.assertEqual(actual, sum(values[w] for w in nodes))
                            else:
                                self.assertEqual(tree.get(v), values[v])
                        u = rng.randrange(n)
                        self.assertEqual(tree.same(u, v), root(u) == root(v))
                        self.assertTrue(tree.same(v, v))
                        self.assertEqual(tree.get(v), values[v])
                        # Reading values and connectivity must preserve roots.
                        for w in (v, rng.randrange(n)):
                            self.assertEqual(tree.parent(w), parent[w])
                            self.assertEqual(tree.root(w), root(w))

    def test_directional_aggregates_after_navigation(self) -> None:
        n = 24
        tree = BidirectionalLinkCutTree(n, '', add)
        values = [chr(ord('a') + v) for v in range(n)]
        tree.build(values[:])
        for v in range(1, n):
            tree.link(v, v - 1)
        rng = random.Random(0)
        for _ in range(300):
            u, v, w = (rng.randrange(n) for _ in range(3))
            tree.reroot(u)
            self.assertTrue(tree.same(u, v))
            self.assertEqual(tree.get(w), values[w])
            self.assertEqual(tree.root(w), u)
            self.assertEqual(tree.parent(w), -1 if w == u else w + (1 if w < u else -1))
            step = 1 if u <= v else -1
            expected = ''.join(values[i] for i in range(u, v + step, step))
            self.assertEqual(tree.path_prod(u, v), (expected, expected[::-1]))


if __name__ == '__main__':
    unittest.main()
