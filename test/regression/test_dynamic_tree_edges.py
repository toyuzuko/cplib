import random
import unittest
from operator import add

from cplib.graph.eulertourtree import EulerTourTree
from cplib.graph.linkcut import BidirectionalLinkCutTree, DynamicTreeAddTreeSum, LazyPathLinkCutTree, LazySubtreeLinkCutTree, LinkCutTree, RerootingLinkCutTreeWithEdges, RerootingLinkCutTree


Forest = LinkCutTree[int] | BidirectionalLinkCutTree[int] | LazyPathLinkCutTree[int, int] | LazySubtreeLinkCutTree[int, int] | DynamicTreeAddTreeSum | RerootingLinkCutTree[int, int, int] | EulerTourTree[int]


def forests(values: list[int]) -> list[Forest]:
    n = len(values)
    result: list[Forest] = [
        LinkCutTree(n, 0, add),
        BidirectionalLinkCutTree(n, 0, add),
        LazyPathLinkCutTree(n, 0, add, lambda f, x, size: x + f * size, add, 0),
        LazySubtreeLinkCutTree(n, 0, add, lambda x: -x, lambda f, x, size: x + f * size, add, lambda f, g: f - g, 0),
        DynamicTreeAddTreeSum(n),
        EulerTourTree(n, 0, add),
    ]
    for tree in result:
        if not isinstance(tree, RerootingLinkCutTree):
            tree.build(values[:])
    result.append(RerootingLinkCutTree(values, 0, add, lambda x: x, add, lambda x: -x, add))
    return result


def root(parent: list[int], v: int) -> int:
    while parent[v] != -1:
        v = parent[v]
    return v


def reroot(parent: list[int], v: int) -> None:
    previous = -1
    while v != -1:
        next_vertex = parent[v]
        parent[v] = previous
        previous, v = v, next_vertex


def subtree(parent: list[int], v: int) -> list[int]:
    nodes = [v]
    for u in nodes:
        nodes.extend(w for w, p in enumerate(parent) if p == u)
    return nodes


class DynamicTreeEdgesTest(unittest.TestCase):
    def check_forest(self, tree: Forest, parent: list[int], values: list[int]) -> None:
        for v, value in enumerate(values):
            self.assertEqual(tree.get(v), value)
            expected_root = root(parent, v)
            if isinstance(tree, RerootingLinkCutTree):
                self.assertEqual(tree.subtree_value(v), sum(values[w] for w in subtree(parent, v)))
            elif isinstance(tree, EulerTourTree):
                component = subtree(parent, expected_root)
                self.assertEqual(set(tree.component_vertices(v)), set(component))
                self.assertEqual(tree.component_aggregate(v), sum(values[w] for w in component))
            else:
                self.assertEqual(tree.root(v), expected_root)
                self.assertEqual(tree.parent(v), parent[v])
                if isinstance(tree, LazySubtreeLinkCutTree):
                    self.assertEqual(tree.subtree_aggregate(v), sum(values[w] for w in subtree(parent, v)))
                elif isinstance(tree, DynamicTreeAddTreeSum):
                    self.assertEqual(tree.subtree_sum(v), sum(values[w] for w in subtree(parent, v)))
            for w in range(len(values)):
                self.assertEqual(tree.same(v, w), expected_root == root(parent, w))

    def test_roles_roots_and_failed_operations(self) -> None:
        values = [1, 2, 4, 8, 16]
        for tree in forests(values):
            with self.subTest(cls=type(tree).__name__):
                self.assertIsNone(tree.link(child=1, parent=0))
                tree.link(child=2, parent=1)
                tree.link(child=4, parent=3)
                # The child endpoint is not the root of its existing tree.
                tree.link(child=1, parent=4)
                parent = [1, 4, 1, -1, 3]
                self.check_forest(tree, parent, values)
                for u, v in [(0, 2), (0, 3), (2, 4), (1, 1)]:
                    with self.assertRaises(ValueError):
                        tree.link(child=u, parent=v)
                    with self.assertRaises(ValueError):
                        tree.cut(u, v)
                    self.check_forest(tree, parent, values)
                for u, v in [(-1, 0), (0, -1), (5, 0), (0, 5)]:
                    with self.assertRaises(IndexError):
                        tree.link(child=u, parent=v)
                    with self.assertRaises(IndexError):
                        tree.cut(u, v)
                    self.check_forest(tree, parent, values)
                if not isinstance(tree, EulerTourTree):
                    with self.assertRaises(ValueError):
                        tree.cut_parent(child=3)
                    for v in (-1, 5):
                        with self.assertRaises(IndexError):
                            tree.cut_parent(child=v)
                    self.check_forest(tree, parent, values)
                self.assertIsNone(tree.cut(4, 1))
                parent = [1, -1, 1, 4, -1]
                self.check_forest(tree, parent, values)
                with self.assertRaises(ValueError):
                    tree.cut(1, 4)
                self.check_forest(tree, parent, values)
                tree.cut(1, 0)
                parent[0] = -1
                self.check_forest(tree, parent, values)

    def test_random_edges_with_updates(self) -> None:
        for seed in range(4):
            n = 10
            for tree in forests(list(range(1, n + 1))):
                rng = random.Random(seed)
                values = list(range(1, n + 1))
                parent = [-1] * n
                for step in range(350):
                    u, v = rng.sample(range(n), 2)
                    op = rng.randrange(7)
                    with self.subTest(cls=type(tree).__name__, seed=seed, step=step, op=op):
                        if op == 0:
                            if root(parent, u) == root(parent, v):
                                with self.assertRaises(ValueError):
                                    tree.link(u, v)
                            else:
                                tree.link(u, v)
                                reroot(parent, u)
                                parent[u] = v
                        elif op == 1:
                            edges = [(w, p) for w, p in enumerate(parent) if p != -1]
                            if edges:
                                child, p = rng.choice(edges)
                                a, b = (child, p) if rng.randrange(2) else (p, child)
                                tree.cut(a, b)
                                parent[child] = -1
                                reroot(parent, p)
                        elif op == 2 and not isinstance(tree, EulerTourTree):
                            if parent[u] == -1:
                                with self.assertRaises(ValueError):
                                    tree.cut_parent(u)
                            else:
                                tree.cut_parent(u)
                                parent[u] = -1
                        elif op == 3:
                            tree.reroot(u)
                            reroot(parent, u)
                        elif op == 4:
                            if parent[u] != v and parent[v] != u:
                                with self.assertRaises(ValueError):
                                    tree.cut(u, v)
                        elif op == 5 and isinstance(tree, (LazySubtreeLinkCutTree, DynamicTreeAddTreeSum)):
                            if isinstance(tree, DynamicTreeAddTreeSum):
                                tree.subtree_add(u, 3)
                            else:
                                tree.subtree_apply(u, 3)
                            for w in subtree(parent, u):
                                values[w] += 3
                        elif op == 5 and isinstance(tree, LazyPathLinkCutTree) and root(parent, u) == root(parent, v):
                            tree.path_apply(u, v, 3)
                            reroot(parent, u)
                            w = v
                            while w != -1:
                                values[w] += 3
                                w = parent[w]
                        else:
                            tree.set(u, step)
                            values[u] = step
                        self.check_forest(tree, parent, values)

    def test_edge_slot_keyword_roles(self) -> None:
        tree = RerootingLinkCutTreeWithEdges(3, 0, add, lambda x: x, add, lambda x: -x, add)
        for v in range(3):
            tree.set_vertex(v, 1 << v)
        edge_id = tree.add_edge(0, 1, 8)
        tree.build()
        tree.cut_edge(edge_id)
        tree.link_edge(edge_id=edge_id, child=1, parent=2)
        self.assertEqual(tree.subtree_value(1), 2)
        self.assertEqual(tree.subtree_value(2), 14)
        self.assertFalse(tree.same(0, 1))

    def test_edge_changes_with_pending_lazy_updates(self) -> None:
        for tree in forests(list(range(1, 9))):
            if not isinstance(tree, (LazyPathLinkCutTree, LazySubtreeLinkCutTree, DynamicTreeAddTreeSum)):
                continue
            with self.subTest(cls=type(tree).__name__):
                for v in range(1, 5):
                    tree.link(v, v - 1)
                if isinstance(tree, LazyPathLinkCutTree):
                    tree.path_apply(0, 4, 10)
                elif isinstance(tree, LazySubtreeLinkCutTree):
                    tree.tree_apply(0, 10)
                else:
                    tree.tree_add(0, 10)
                with self.assertRaises(ValueError):
                    tree.cut(0, 4)
                tree.cut(3, 2)
                tree.link(child=4, parent=6)
                tree.cut(4, 3)
                self.check_forest(tree, [1, 2, -1, -1, -1, -1, 4, -1], [11, 12, 13, 14, 15, 6, 7, 8])

    def test_euler_tour_link_preserves_parent_tour_start(self) -> None:
        tree = EulerTourTree(6, 0, add)
        tree.link(child=1, parent=0)
        tree.link(child=2, parent=1)
        tree.link(child=4, parent=3)
        tree.link(child=5, parent=4)
        tree.reroot(3)
        tree.link(child=1, parent=5)
        self.assertEqual(tree.component_vertices(0)[0], 3)


if __name__ == '__main__':
    unittest.main()
