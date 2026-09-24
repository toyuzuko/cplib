import random
import unittest
from operator import add

from cplib.graph.connectivity import HDLTOnlineDynamicConnectivity, SimpleOnlineDynamicConnectivity
from cplib.graph.eulertourtree import EulerTourTree


class EulerTourReuseTest(unittest.TestCase):
    def test_repeated_cut_and_link_use_bounded_storage(self) -> None:
        tree = EulerTourTree(2, 0, add)
        tree.build([10, 20])
        tree.set_mark(1, 1)
        for _ in range(2000):
            tree.link(0, 1)
            self.assertEqual(tree.component_aggregate(0), 30)
            self.assertEqual(tree.find_marked(0), 1)
            tree.cut(1, 0)
            self.assertFalse(tree.same(0, 1))
            self.assertEqual(tree.component_aggregate(0), 10)
            self.assertEqual(tree.component_aggregate(1), 20)
            self.assertEqual(tree.find_marked(0), -1)
            self.assertEqual(tree.find_marked(1), 1)
        self.assertEqual(len(tree.val), 5)
        self.assertEqual(len(tree.edge_node), 0)

    def test_recycled_edges_preserve_values_sizes_and_markers(self) -> None:
        for seed in range(5):
            rng = random.Random(seed)
            n = 18
            values = [rng.randrange(-10, 11) for _ in range(n)]
            marks = [0] * n
            graph: list[set[int]] = [set() for _ in range(n)]
            edges: set[tuple[int, int]] = set()
            tree = EulerTourTree(n, 0, add)
            tree.build(values)
            peak = 0

            def component(v: int) -> set[int]:
                found = {v}
                stack = [v]
                for u in stack:
                    for w in graph[u]:
                        if w not in found:
                            found.add(w)
                            stack.append(w)
                return found

            for step in range(1000):
                u, v = rng.randrange(n), rng.randrange(n)
                op = rng.randrange(5)
                if op == 0 and v not in component(u):
                    tree.link(u, v)
                    graph[u].add(v)
                    graph[v].add(u)
                    edges.add(tuple(sorted((u, v))))
                    peak = max(peak, len(edges))
                elif op == 1 and edges:
                    a, b = rng.choice(sorted(edges))
                    tree.cut(a, b)
                    edges.remove((a, b))
                    graph[a].remove(b)
                    graph[b].remove(a)
                elif op == 2:
                    values[u] = rng.randrange(-10, 11)
                    tree.set(u, values[u])
                elif op == 3:
                    marks[u] = rng.randrange(3)
                    tree.set_mark(u, marks[u])
                else:
                    tree.reroot(u)
                with self.subTest(seed=seed, step=step):
                    nodes = component(u)
                    self.assertEqual(tree.same(u, v), v in nodes)
                    self.assertEqual(tree.get(u), values[u])
                    self.assertEqual(tree.component_size(u), len(nodes))
                    self.assertEqual(tree.component_aggregate(u), sum(values[w] for w in nodes))
                    self.assertEqual(set(tree.component_vertices(u)), nodes)
                    marked = {w for w in nodes if marks[w]}
                    self.assertEqual(tree.component_has_marked(u), bool(marked))
                    self.assertIn(tree.find_marked(u), marked if marked else {-1})
                    self.assertLessEqual(len(tree.val), n + 2 * peak + 1)

    def test_dynamic_connectivity_with_replacement_edges(self) -> None:
        for cls in (SimpleOnlineDynamicConnectivity, HDLTOnlineDynamicConnectivity):
            rng = random.Random(0)
            n = 12
            values = list(range(n))
            graph: list[set[int]] = [set() for _ in range(n)]
            tree = cls(n, 0, add, values)
            for step in range(1500):
                u, v = rng.sample(range(n), 2)
                if rng.randrange(5) == 0:
                    values[u] = rng.randrange(-10, 11)
                    tree.set(u, values[u])
                elif v in graph[u]:
                    tree.erase_edge(u, v)
                    graph[u].remove(v)
                    graph[v].remove(u)
                else:
                    tree.insert_edge(u, v)
                    graph[u].add(v)
                    graph[v].add(u)
                nodes = {u}
                stack = [u]
                for w in stack:
                    for z in graph[w]:
                        if z not in nodes:
                            nodes.add(z)
                            stack.append(z)
                with self.subTest(cls=cls.__name__, step=step):
                    self.assertEqual(tree.same(u, v), v in nodes)
                    self.assertEqual(tree.component_size(u), len(nodes))
                    self.assertEqual(tree.component_aggregate(u), sum(values[w] for w in nodes))
            forests = tree.forest if isinstance(tree, HDLTOnlineDynamicConnectivity) else [tree.forest]
            for forest in forests:
                self.assertLessEqual(len(forest.val), 3 * n - 1)


if __name__ == '__main__':
    unittest.main()
