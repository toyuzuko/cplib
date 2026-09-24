import random
import unittest
from operator import add

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.toptree import StaticTopTree, StaticTopTreeWithEdges, TopTree, TopTreeWithEdges
from test.regression.test_static_top_tree_balance import MOD, compress, edge_cluster, rake, vertex_cluster


def rooted_forest(n: int, edges: list[tuple[int, int] | None], root: int) -> tuple[list[int], list[int], list[int]]:
    adjacency: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for edge_id, edge in enumerate(edges):
        if edge is not None:
            u, v = edge
            adjacency[u].append((v, edge_id))
            adjacency[v].append((u, edge_id))
    parents = [-2] * n
    incoming = [-1] * n
    parents[root] = -1
    order = [root]
    for vertex in order:
        for child, edge_id in adjacency[vertex]:
            if child != parents[vertex]:
                parents[child] = vertex
                incoming[child] = edge_id
                order.append(child)
    return parents, incoming, order


class TopTreeCommonTest(unittest.TestCase):
    def test_common_vertex_callbacks_and_none_aggregates(self) -> None:
        rng = random.Random(0)
        for n in (1, 2, 50):
            graph = Tree(n)
            values = [rng.randrange(100) for _ in range(n)]
            dynamic = TopTree(values, 0, max, lambda path: path, max, max)
            for child in range(1, n):
                parent = rng.randrange(child)
                graph.add_edge(Node(child), Node(parent))
                dynamic.link(child, parent)
            graph.build(Node(0))
            static = StaticTopTree(graph, values, 0, max, lambda path: path, max, max)
            for _ in range(80):
                vertex, value = rng.randrange(n), rng.randrange(100)
                static.set(vertex, value)
                dynamic.set(vertex, value)
                values[vertex] = value
                self.assertEqual(static.get(vertex), dynamic.get(vertex))
                self.assertEqual(static.tree_value(), max(values))
                self.assertEqual(static.tree_value(), dynamic.tree_value(0))
                for vertex in range(n):
                    self.assertEqual(static.subtree_value(vertex), dynamic.subtree_value(vertex))
            # None is a legitimate payload, identity, and aggregate, not a sentinel.
            for cls, args in ((StaticTopTree, (graph,)), (TopTree, ())):
                top = cls(*args, [None] * n, None, lambda point, value: None,
                          lambda path: None, lambda a, b: None, lambda a, b: None)
                if cls is TopTree:
                    for child in range(1, n):
                        top.link(child, int(graph.par_v[child]))
                top.set(0, None)
                self.assertIsNone(top.get(0))
                self.assertIsNone(top.subtree_value(0))
                self.assertIsNone(top.tree_value() if cls is StaticTopTree else top.tree_value(0))

    def test_edge_callbacks_match_static_dynamic_and_naive(self) -> None:
        for seed in range(5):
            rng = random.Random(seed)
            n = 1 if seed == 0 else 25
            graph = Tree(n)
            edges = [(child, rng.randrange(child)) for child in range(1, n)]
            for u, v in edges:
                graph.add_edge(Node(u), Node(v))
            root = rng.randrange(n)
            graph.build(Node(root))
            values = [rng.randrange(MOD) for _ in range(n)]
            payloads = [(rng.randrange(MOD), rng.randrange(MOD)) for _ in edges]
            callbacks = ((0, 0), vertex_cluster, edge_cluster, lambda path: (path[2], path[3]), rake, compress)
            static = StaticTopTreeWithEdges(graph, values, payloads, *callbacks)
            dynamic = TopTreeWithEdges(values, edges, payloads, *callbacks)
            for step in range(70):
                if edges and rng.randrange(2):
                    edge_id = rng.randrange(len(edges))
                    payloads[edge_id] = rng.randrange(MOD), rng.randrange(MOD)
                    for top in (static, dynamic):
                        top.set_edge(edge_id, payloads[edge_id])
                        self.assertEqual(top.get_edge(edge_id), payloads[edge_id])
                else:
                    vertex = rng.randrange(n)
                    values[vertex] = rng.randrange(MOD)
                    for top in (static, dynamic):
                        top.set_vertex(vertex, values[vertex])
                        self.assertEqual(top.get_vertex(vertex), values[vertex])
                self.assertEqual(static.tree_value()[2:], dynamic.tree_value(root)[2:])
                for vertex in range(n):
                    self.assertEqual(static.subtree_value(vertex)[2:], dynamic.subtree_value(vertex)[2:])
                new_root = rng.randrange(n)
                parents, incoming, order = rooted_forest(n, edges, new_root)
                expected, sizes = values[:], [1] * n
                for vertex in reversed(order[1:]):
                    a, b = payloads[incoming[vertex]]
                    parent = parents[vertex]
                    expected[parent] = (expected[parent] + a * expected[vertex] + b * sizes[vertex]) % MOD
                    sizes[parent] += sizes[vertex]
                dynamic.reroot(new_root)
                for vertex in range(n):
                    with self.subTest(seed=seed, step=step, vertex=vertex):
                        self.assertEqual(dynamic.subtree_value(vertex)[2:], (expected[vertex], sizes[vertex]))
                        self.assertEqual(dynamic.parent(vertex), parents[vertex])
                        self.assertEqual(dynamic.root(vertex), new_root)

    def test_edge_slots_cuts_relinks_and_failed_operations(self) -> None:
        rng = random.Random(42)
        n = 24
        edges: list[tuple[int, int] | None] = [(child, rng.randrange(child)) for child in range(1, n)]
        values = [rng.randrange(100) for _ in range(n)]
        payloads = [rng.randrange(100) for _ in edges]
        top = TopTreeWithEdges(values, edges, payloads, 0, add, add, lambda path: path, add, add)
        roots = [0] * n
        for step in range(600):
            operation = rng.randrange(5)
            active = [edge_id for edge_id, edge in enumerate(edges) if edge is not None]
            detached = [edge_id for edge_id, edge in enumerate(edges) if edge is None]
            if operation == 0 and active:
                edge_id = rng.choice(active)
                u, v = edges[edge_id]
                top.cut_edge(edge_id)
                edges[edge_id] = None
                for root in (u, v):
                    for vertex in rooted_forest(n, edges, root)[2]:
                        roots[vertex] = root
                with self.assertRaises(ValueError):
                    top.cut_edge(edge_id)
            elif operation == 1 and detached:
                edge_id = rng.choice(detached)
                child, parent = rng.sample(range(n), 2)
                if roots[child] == roots[parent]:
                    with self.assertRaises(ValueError):
                        top.link_edge(edge_id, child, parent)
                else:
                    root = roots[parent]
                    top.link_edge(edge_id, child, parent)
                    edges[edge_id] = child, parent
                    for vertex in rooted_forest(n, edges, root)[2]:
                        roots[vertex] = root
            elif operation == 2:
                vertex = rng.randrange(n)
                values[vertex] = rng.randrange(100)
                top.set_vertex(vertex, values[vertex])
            elif operation == 3:
                edge_id = rng.randrange(len(edges))
                payloads[edge_id] = rng.randrange(100)
                top.set_edge(edge_id, payloads[edge_id])
            else:
                root = rng.randrange(n)
                top.reroot(root)
                for vertex in rooted_forest(n, edges, root)[2]:
                    roots[vertex] = root
            for root in set(roots):
                parents, incoming, order = rooted_forest(n, edges, root)
                expected = values[:]
                for vertex in reversed(order[1:]):
                    expected[parents[vertex]] += expected[vertex] + payloads[incoming[vertex]]
                for vertex in order:
                    with self.subTest(step=step, vertex=vertex):
                        self.assertEqual(top.root(vertex), root)
                        self.assertEqual(top.parent(vertex), parents[vertex])
                        self.assertEqual(top.subtree_value(vertex), expected[vertex])
                self.assertEqual(top.tree_value(root), expected[root])
                self.assertEqual(top.path_cluster_value(root, order[-1]), expected[root])
            u, v = rng.sample(range(n), 2)
            self.assertEqual(top.same(u, v), roots[u] == roots[v])
            if roots[u] != roots[v]:
                with self.assertRaises(ValueError):
                    top.subtree_value(u, root=v)
                with self.assertRaises(ValueError):
                    top.path_cluster_value(u, v)
            if active and edges[active[0]] is not None:
                with self.assertRaises(ValueError):
                    top.link_edge(active[0], u, v)
            self.assertEqual([top.root(v) for v in range(n)], roots)

    def test_inverse_free_edge_maximum_and_initial_disconnected_forest(self) -> None:
        top = TopTreeWithEdges([2, 3, 4, 5], [(0, 1), (2, 3)], [100, 20],
                               0, max, max, lambda path: path, max, max)
        self.assertFalse(top.same(0, 2))
        self.assertEqual(top.tree_value(0), 100)
        self.assertEqual(top.tree_value(2), 20)
        top.cut_edge(0)
        self.assertEqual(top.tree_value(0), 2)
        self.assertEqual(top.tree_value(1), 3)
        top.set_edge(0, 50)
        top.link_edge(0, 1, 2)
        self.assertEqual(top.root(1), 2)
        self.assertEqual(top.tree_value(2), 50)
        self.assertEqual(top.subtree_value(1), 3)
        top.set_edge(0, 1)
        self.assertEqual(top.tree_value(2), 20)
        top.set_vertex(3, 200)
        self.assertEqual(top.tree_value(1), 200)
        top.cut_edge(1)
        self.assertEqual(top.tree_value(1), 4)
        self.assertEqual(top.tree_value(3), 200)

    def test_validation_and_empty_forests(self) -> None:
        callbacks = (0, add, add, lambda path: path, add, add)
        empty = TopTreeWithEdges([], [], [], *callbacks)
        with self.assertRaises(IndexError):
            empty.tree_value(0)
        for edges, payloads, error in [([(0, 0)], [0], ValueError), ([(0, 1), (0, 1)], [0, 0], ValueError), ([(0, 2)], [0], IndexError), ([(0, -1)], [0], IndexError), ([(0, 1)], [], ValueError)]:
            with self.assertRaises(error):
                TopTreeWithEdges([1, 2], edges, payloads, *callbacks)
        graph = Tree(2)
        with self.assertRaises(ValueError):
            StaticTopTree(graph, [1, 2], 0, add, lambda path: path, add, add)
        with self.assertRaises(ValueError):
            StaticTopTreeWithEdges(graph, [1, 2], [0], *callbacks)
        graph.add_edge(Node(0), Node(1))
        graph.build()
        with self.assertRaises(ValueError):
            StaticTopTree(graph, [1], 0, add, lambda path: path, add, add)
        with self.assertRaises(ValueError):
            StaticTopTreeWithEdges(graph, [1, 2], [], *callbacks)
        static = StaticTopTree(graph, [1, 2], 0, add, lambda path: path, add, add)
        for index in (-1, 2):
            for method, args in ((static.get, (index,)), (static.set, (index, 0)), (static.subtree_value, (index,))):
                with self.assertRaises(IndexError):
                    method(*args)
        structures = (StaticTopTreeWithEdges(graph, [1, 2], [3], *callbacks),
                      TopTreeWithEdges([1, 2], [(0, 1)], [3], *callbacks))
        for top in structures:
            for index in (-1, 2):
                for method, args in ((top.get_vertex, (index,)), (top.set_vertex, (index, 9)), (top.subtree_value, (index,))):
                    with self.assertRaises(IndexError):
                        method(*args)
            for index in (-1, 1):
                with self.assertRaises(IndexError):
                    top.get_edge(index)
                with self.assertRaises(IndexError):
                    top.set_edge(index, 9)
            self.assertEqual(top.get_vertex(0), 1)
            self.assertEqual(top.get_edge(0), 3)
        dynamic = structures[1]
        dynamic.cut_edge(0)
        dynamic.set_edge(0, 100)
        dynamic.link_edge(0, 0, 1)
        for method, args in ((dynamic.cut_edge, (-1,)), (dynamic.link_edge, (1, 0, 1)),
                             (dynamic.link_edge, (0, -1, 0)), (dynamic.root, (2,)),
                             (dynamic.parent, (2,)), (dynamic.reroot, (2,)),
                             (dynamic.same, (0, 2)), (dynamic.tree_value, (2,)),
                             (dynamic.path_cluster_value, (0, 2)), (dynamic.subtree_value, (0, 2))):
            with self.assertRaises(IndexError):
                method(*args)
        self.assertEqual(dynamic.tree_value(1), 103)


if __name__ == '__main__':
    unittest.main()
