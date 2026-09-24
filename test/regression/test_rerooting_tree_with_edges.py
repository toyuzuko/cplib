import random
import unittest
from operator import add

from cplib.graph.linkcut import RerootingLinkCutTreeWithEdges


def sum_tree(n: int) -> RerootingLinkCutTreeWithEdges[int, int, int]:
    return RerootingLinkCutTreeWithEdges(n, 0, add, lambda x: x, add, lambda x: -x, add)


class RerootingTreeWithEdgesTest(unittest.TestCase):
    def test_vertex_edge_access_and_subtree_boundary(self) -> None:
        tree = sum_tree(4)
        for v, value in enumerate([1, 2, 4, 8]):
            tree.set_vertex(v, value)
        for u, v, value in [(0, 1, 10), (1, 2, 20), (1, 3, 40)]:
            tree.add_edge(u, v, value)
        tree.set_edge(2, 50)
        self.assertEqual(tree.get_vertex(2), 4)
        self.assertEqual(tree.get_edge(2), 50)
        tree.build(2)
        self.assertEqual(tree.subtree_value(1), 71)
        tree.reroot(0)
        self.assertEqual(tree.subtree_value(1), 84)
        self.assertEqual(tree.path_cluster_value(0, 2), 95)
        tree.set_vertex(1, 3)
        tree.set_edge(1, 30)
        self.assertEqual(tree.tree_value(3), 106)
        tree.set(tree.es[0], 60)
        tree.set(tree.vs[0], 9)
        self.assertEqual(tree.get_edge(0), 60)
        self.assertEqual(tree.get_vertex(0), 9)
        self.assertEqual(tree.get(tree.es[1]), 30)
        self.assertEqual(tree.tree_value(0), 164)

    def test_cut_relink_and_rejected_operations(self) -> None:
        tree = sum_tree(3)
        for v in range(3):
            tree.set_vertex(v, v + 1)
        tree.add_edge(0, 1, 10)
        tree.add_edge(1, 2, 20)
        tree.build()
        tree.cut_edge(0)
        self.assertFalse(tree.same(0, 2))
        self.assertEqual(tree.tree_value(0), 1)
        self.assertEqual(tree.tree_value(1), 25)
        tree.set_edge(0, 50)
        self.assertEqual(tree.get_edge(0), 50)
        with self.assertRaises(ValueError):
            tree.cut_edge(0)
        with self.assertRaises(ValueError):
            tree.link_edge(0, 1, 2)
        with self.assertRaises(ValueError):
            tree.link_edge(1, 0, 1)
        with self.assertRaises(ValueError):
            tree.path_cluster_value(0, 1)
        with self.assertRaises(ValueError):
            tree.subtree_value(0, root=1)
        self.assertEqual(tree.tree_value(1), 25)
        tree.link_edge(0, 0, 2)
        self.assertEqual(tree.tree_value(0), 76)
        self.assertEqual(tree.subtree_value(2, root=0), 25)
        self.assertEqual(tree.es, [3, 4])
        for _ in range(100):
            tree.cut_edge(0)
            tree.link_edge(0, 0, 2)
        self.assertEqual(tree.tree_value(2), 76)
        assert tree.lct is not None
        self.assertEqual(tree.lct.n, 5)

    def test_registration_and_disconnected_initial_forest(self) -> None:
        tree = sum_tree(4)
        with self.assertRaises(ValueError):
            tree.get_vertex(0)
        with self.assertRaises(ValueError):
            tree.build()
        with self.assertRaises(ValueError):
            tree.tree_value(0)
        for v in range(4):
            tree.set_vertex(v, v + 1)
        tree.add_edge(0, 1, 10)
        with self.assertRaises(ValueError):
            tree.add_edge(1, 2, 20, edge_id=0)
        tree.build(3)
        self.assertEqual(tree.tree_value(0), 13)
        self.assertEqual(tree.tree_value(2), 3)
        self.assertEqual(tree.subtree_value(3), 4)
        tree.cut_edge(0)
        tree.link_edge(0, 2, 3)
        self.assertEqual(tree.tree_value(2), 17)
        with self.assertRaises(ValueError):
            tree.build()
        with self.assertRaises(ValueError):
            tree.add_edge(0, 1, 0)
        with self.assertRaises(IndexError):
            tree.get_vertex(-1)
        with self.assertRaises(IndexError):
            tree.get_edge(1)
        for edges in [[(0, 1), (1, 0)], [(0, 1), (1, 2), (2, 0)]]:
            invalid = sum_tree(3)
            for v in range(3):
                invalid.set_vertex(v, 0)
            for u, v in edges:
                invalid.add_edge(u, v, 0)
            with self.assertRaises(ValueError):
                invalid.build()
            self.assertIsNone(invalid.lct)
        single = sum_tree(1)
        single.set_vertex(0, 7)
        single.build()
        self.assertEqual(single.path_cluster_value(0, 0), 7)

    def test_random_forest_with_edge_payloads(self) -> None:
        for seed in range(10):
            rng = random.Random(seed)
            n = 18
            vertices = [rng.randrange(-10, 11) for _ in range(n)]
            values = [rng.randrange(-10, 11) for _ in range(n - 1)]
            endpoints = [(v, rng.randrange(v)) for v in range(1, n)]
            adjacency: list[dict[int, int]] = [{} for _ in range(n)]
            active = [True] * (n - 1)
            roots = {0}
            tree = sum_tree(n)
            for v, value in enumerate(vertices):
                tree.set_vertex(v, value)
            for edge_id, (u, v) in enumerate(endpoints):
                tree.add_edge(u, v, values[edge_id])
                adjacency[u][v] = adjacency[v][u] = edge_id
            tree.build()

            def component(v: int, blocked: int = -1) -> list[int]:
                nodes = [v]
                seen = {v, blocked}
                for u in nodes:
                    for w in adjacency[u]:
                        if w not in seen:
                            seen.add(w)
                            nodes.append(w)
                return nodes

            def naive_root(v: int) -> int:
                return next(iter(roots.intersection(component(v))))

            def reroot(v: int) -> None:
                roots.remove(naive_root(v))
                roots.add(v)

            def total(nodes: list[int]) -> int:
                included = set(nodes)
                edges = {edge_id for u in nodes for v, edge_id in adjacency[u].items() if v in included}
                return sum(vertices[u] for u in nodes) + sum(values[e] for e in edges)

            for step in range(500):
                v = rng.randrange(n)
                edge_id = rng.randrange(n - 1)
                value = rng.randrange(-20, 21)
                op = rng.randrange(10)
                with self.subTest(seed=seed, step=step, op=op):
                    if op == 0:
                        tree.set_vertex(v, value)
                        vertices[v] = value
                    elif op == 1:
                        tree.set_edge(edge_id, value)
                        values[edge_id] = value
                    elif op == 2 and active[edge_id]:
                        u, w = endpoints[edge_id]
                        roots.remove(naive_root(u))
                        tree.cut_edge(edge_id)
                        del adjacency[u][w]
                        del adjacency[w][u]
                        roots.update((u, w))
                        active[edge_id] = False
                    elif op == 3 and not active[edge_id]:
                        u, w = rng.randrange(n), rng.randrange(n)
                        if w not in component(u):
                            roots.remove(naive_root(u))
                            tree.link_edge(edge_id, u, w)
                            adjacency[u][w] = adjacency[w][u] = edge_id
                            endpoints[edge_id] = (u, w)
                            active[edge_id] = True
                    elif op == 4:
                        self.assertEqual(tree.tree_value(v), total(component(v)))
                        reroot(v)
                    elif op == 5:
                        new_root = rng.choice(component(v)) if rng.randrange(2) else None
                        if new_root is not None:
                            reroot(new_root)
                        parent = {naive_root(v): -1}
                        order = [naive_root(v)]
                        for u in order:
                            for w in adjacency[u]:
                                if w not in parent:
                                    parent[w] = u
                                    order.append(w)
                        expected = total(component(v, parent[v]))
                        self.assertEqual(tree.subtree_value(v, root=new_root), expected)
                    elif op == 6:
                        tree.reroot(v)
                        reroot(v)
                    elif op == 7:
                        w = rng.choice(component(v))
                        self.assertEqual(tree.path_cluster_value(v, w), total(component(v)))
                        reroot(v)
                    elif op == 8:
                        w = rng.randrange(n)
                        self.assertEqual(tree.same(v, w), w in component(v))
                    elif op == 9:
                        tree.set(tree.es[edge_id], value)
                        values[edge_id] = value
                    self.assertEqual(tree.get_vertex(v), vertices[v])
                    self.assertEqual(tree.get_edge(edge_id), values[edge_id])

    def test_affine_dp_after_vertex_edge_and_topology_updates(self) -> None:
        mod = 998244353

        def add_vertex(point: tuple[int, int], info: tuple[bool, int, int]) -> tuple[int, int, int, int]:
            is_vertex, a, b = info
            total, count = point
            if is_vertex:
                return 1, 0, (total + a) % mod, count + 1
            return a, b, (a * total + b * count) % mod, count

        def compress(upper: tuple[int, int, int, int], lower: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
            a, b, total, count = upper
            c, d, other_total, other_count = lower
            return a * c % mod, (a * d + b) % mod, (total + a * other_total + b * other_count) % mod, count + other_count

        n = 12
        rng = random.Random(0)
        vertices = [rng.randrange(20) for _ in range(n)]
        edges = [(rng.randrange(5), rng.randrange(5)) for _ in range(n - 1)]
        endpoints = [(v, rng.randrange(v)) for v in range(1, n)]
        adjacency: list[dict[int, int]] = [{} for _ in range(n)]
        tree = RerootingLinkCutTreeWithEdges(
            n, (0, 0), add_vertex, lambda path: (path[2], path[3]),
            lambda a, b: ((a[0] + b[0]) % mod, a[1] + b[1]),
            lambda a: (-a[0] % mod, -a[1]), compress,
        )
        for v, value in enumerate(vertices):
            tree.set_vertex(v, (True, value, 0))
        for e, (u, v) in enumerate(endpoints):
            tree.add_edge(u, v, (False, *edges[e]))
            adjacency[u][v] = adjacency[v][u] = e
        tree.build()

        def rooted_order(root: int) -> tuple[list[int], dict[int, tuple[int, int]]]:
            parent = {root: (-1, -1)}
            order = [root]
            for v in order:
                for u, e in adjacency[v].items():
                    if u not in parent:
                        parent[u] = (v, e)
                        order.append(u)
            return order, parent

        def naive(root: int) -> list[int]:
            order, parent = rooted_order(root)
            totals, counts = vertices[:], [1] * n
            for v in reversed(order[1:]):
                p, e = parent[v]
                a, b = edges[e]
                totals[p] = (totals[p] + a * totals[v] + b * counts[v]) % mod
                counts[p] += counts[v]
            return totals

        for step in range(250):
            vertex, edge_id = rng.randrange(n), rng.randrange(n - 1)
            if step % 3 == 0:
                vertices[vertex] = rng.randrange(30)
                tree.set_vertex(vertex, (True, vertices[vertex], 0))
            elif step % 3 == 1:
                edges[edge_id] = rng.randrange(5), rng.randrange(5)
                tree.set_edge(edge_id, (False, *edges[edge_id]))
            else:
                u, v = endpoints[edge_id]
                tree.cut_edge(edge_id)
                del adjacency[u][v]
                del adjacency[v][u]
                self.assertEqual(tree.tree_value(u)[2], naive(u)[u])
                self.assertEqual(tree.tree_value(v)[2], naive(v)[v])
                u = rng.choice(rooted_order(u)[0])
                v = rng.choice(rooted_order(v)[0])
                tree.link_edge(edge_id, u, v)
                adjacency[u][v] = adjacency[v][u] = edge_id
                endpoints[edge_id] = u, v
            root = rng.randrange(n)
            expected = naive(root)
            with self.subTest(step=step, root=root):
                self.assertEqual(tree.tree_value(root)[2], expected[root])
                self.assertEqual(tree.subtree_value(vertex)[2], expected[vertex])
                self.assertEqual(tree.path_cluster_value(root, vertex)[2], expected[root])


if __name__ == '__main__':
    unittest.main()
