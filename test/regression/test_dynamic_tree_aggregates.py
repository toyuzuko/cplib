import random
import unittest

from cplib.graph.linkcut import DynamicTreeAddTreeSum, LazySubtreeLinkCutTree, RerootingLinkCutTree


class DynamicTreeAggregatesTest(unittest.TestCase):
    def test_whole_tree_after_point_access(self) -> None:
        tree = DynamicTreeAddTreeSum(3)
        tree.build([1, 2, 3])
        tree.link(1, 0)
        tree.link(2, 1)
        tree.reroot(0)
        tree.get(2)
        self.assertEqual(tree.tree_sum(0), 6)
        tree.get(2)
        tree.tree_add(0, 10)
        self.assertEqual([tree.get(v) for v in range(3)], [11, 12, 13])
        self.assertEqual([tree.parent(v) for v in range(3)], [-1, 0, 1])

    def test_generic_whole_tree_updates(self) -> None:
        tree = LazySubtreeLinkCutTree[tuple[int, int], tuple[int, int]](
            4, (0, 0),
            lambda a, b: (a[0] + b[0], a[1] + b[1]),
            lambda a: (-a[0], -a[1]),
            lambda f, a, n: (a[0] + f[0] * n, a[1] + f[1] * n),
            lambda f, g: (f[0] + g[0], f[1] + g[1]),
            lambda f, g: (f[0] - g[0], f[1] - g[1]), (0, 0),
        )
        tree.build([(1, 10), (2, 20), (3, 30), (4, 40)])
        for v in (1, 2, 3):
            tree.link(v, 0)
        tree.get(1)
        tree.tree_apply(2, (5, -2))
        tree.subtree_apply(0, (1, 3), root=1)
        self.assertEqual(tree.tree_aggregate(3), (33, 101))
        self.assertEqual([tree.get(v) for v in range(4)], [(7, 11), (7, 18), (9, 31), (10, 41)])
        self.assertEqual(tree.root(3), 1)

    def test_random_forest_against_naive(self) -> None:
        for seed in range(12):
            rng = random.Random(seed)
            n = 16
            values = [rng.randrange(-20, 21) for _ in range(n)]
            parent = [-1] + [rng.randrange(v) for v in range(1, n)]
            tree = DynamicTreeAddTreeSum(n)
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

            for step in range(500):
                v = rng.randrange(n)
                value = rng.randrange(-10, 11)
                op = rng.randrange(10)
                with self.subTest(seed=seed, step=step, op=op):
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
                    elif op == 4:
                        self.assertEqual(tree.get(v), values[v])
                    elif op == 5:
                        tree.tree_add(v, value)
                        for u in subtree(root(v)):
                            values[u] += value
                    elif op == 6:
                        self.assertEqual(tree.tree_sum(v), sum(values[u] for u in subtree(root(v))))
                    elif op in (7, 8):
                        new_root = rng.choice(subtree(root(v))) if rng.randrange(2) else None
                        if new_root is not None:
                            reroot(new_root)
                        nodes = subtree(v)
                        if op == 7:
                            tree.subtree_add(v, value, root=new_root)
                            for u in nodes:
                                values[u] += value
                        else:
                            self.assertEqual(tree.subtree_sum(v, root=new_root), sum(values[u] for u in nodes))
                    else:
                        tree.access(v)
                    self.assertEqual(tree.parent(v), parent[v])
                    self.assertEqual(tree.root(v), root(v))
            self.assertEqual([tree.get(v) for v in range(n)], values)

    def test_rerooting_path_cluster_includes_branches(self) -> None:
        tree = RerootingLinkCutTree(
            [1, 2, 4, 8], 0, lambda p, v: p + v, lambda p: p,
            lambda a, b: a + b, lambda a: -a, lambda a, b: a + b,
        )
        for v in (1, 2, 3):
            tree.link(v, 0)
        self.assertEqual(tree.path_cluster_value(1, 2), 15)
        self.assertEqual(tree.subtree_value(0), 13)
        self.assertEqual(tree.subtree_value(0, root=0), 15)
        tree.set(3, 16)
        self.assertEqual(tree.path_cluster_value(0, 2), 23)


if __name__ == '__main__':
    unittest.main()
