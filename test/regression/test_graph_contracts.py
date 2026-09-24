import random
import unittest

from cplib.graph.base import Capacity, Node, Weight
from cplib.graph.core import CSRGraph, Graph, Tree
from cplib.graph.flow import BipartiteMatching, MaximumFlow, MinimumCostBFlow
from cplib.graph.matching import BipartiteMaximumMatching, MatchingSuccess
from cplib.graph.tree import TreeHashContext, tree_diameter


class GraphContractsTest(unittest.TestCase):
    def test_vertex_validation_before_mutation(self) -> None:
        with self.assertRaises(ValueError):
            MinimumCostBFlow(-1)
        for cls in (Graph, Tree, MaximumFlow):
            with self.subTest(cls=cls.__name__):
                with self.assertRaises(ValueError):
                    cls(-1)
                graph = cls(2)
                for u, v in [(-1, 0), (0, -1), (2, 0), (0, 2)]:
                    with self.assertRaises(IndexError):
                        graph.add_edge(Node(u), Node(v), 1)
                    self.assertEqual(graph.m, 0)
                    self.assertEqual(graph.edges, [])
        with self.assertRaises(ValueError):
            CSRGraph(-1, [])
        for vertex in (-1, 2):
            with self.assertRaises(IndexError):
                CSRGraph(2, [(Node(vertex), Node(0))])
            csr = CSRGraph(2, [])
            for query in (csr.adjacent_range, csr.out_degree, csr.neighbors, csr.neighbor_edges, csr.weighted_neighbor_edges):
                with self.assertRaises(IndexError):
                    result = query(Node(vertex))
                    if not isinstance(result, int):
                        list(result)
        tree = Tree(2)
        tree.add_edge(Node(0), Node(1))
        for vertex in (-1, 2):
            with self.assertRaises(IndexError):
                tree.build(Node(vertex))
            self.assertEqual(tree.root, -1)
            with self.assertRaises(IndexError):
                TreeHashContext().rooted_tree_id(tree, Node(vertex))

    def test_invalid_flow_queries_preserve_flow(self) -> None:
        graph = MaximumFlow(2)
        graph.add_edge(Node(0), Node(1), Capacity(3))
        self.assertEqual(graph.solve(Node(0), Node(1), Capacity(1)).flow, 1)
        before = graph.get_edges()
        for source, target, limit, error in [(0, 0, None, ValueError), (-1, 1, None, IndexError), (0, 2, None, IndexError), (0, 1, -1, ValueError)]:
            with self.assertRaises(error):
                graph.solve(Node(source), Node(target), limit)
            self.assertEqual(graph.get_edges(), before)
        with self.assertRaises(ValueError):
            graph.add_edge(Node(0), Node(1), Capacity(-1))
        self.assertEqual(graph.get_edges(), before)
        for edge in (-1, 1):
            with self.assertRaises(IndexError):
                graph.get_edge(edge)
        self.assertEqual(graph.solve(Node(0), Node(1), Capacity(0)).flow, 0)
        self.assertEqual(graph.get_edges(), before)
        self.assertEqual(graph.solve(Node(0), Node(1)).flow, 2)

    def test_repeated_flow_against_minimum_cut(self) -> None:
        rng = random.Random(0)
        for _ in range(80):
            n = rng.randrange(2, 8)
            graph = MaximumFlow(n)
            edges = [(rng.randrange(n), rng.randrange(n), rng.randrange(6)) for _ in range(20)]
            for u, v, capacity in edges:
                graph.add_edge(Node(u), Node(v), Capacity(capacity))
            expected = min(sum(c for u, v, c in edges if mask >> u & 1 and not mask >> v & 1)
                           for mask in range(1 << n) if mask & 1 and not mask >> (n - 1) & 1)
            total = 0
            for limit in (0, 1, 2, 3, None):
                result = graph.solve(Node(0), Node(n - 1), limit)
                total += result.flow
                balance = [0] * n
                for edge in result.edges:
                    self.assertLessEqual(0, edge.flow)
                    self.assertLessEqual(edge.flow, edge.capacity)
                    balance[edge.source] -= edge.flow
                    balance[edge.target] += edge.flow
                self.assertEqual(balance, [-total] + [0] * (n - 2) + [total])
            self.assertEqual(total, expected)
            self.assertEqual(graph.solve(Node(0), Node(n - 1)).flow, 0)
            graph.add_edge(Node(0), Node(n - 1), Capacity(4))
            self.assertEqual(graph.solve(Node(0), Node(n - 1)).flow, 4)

    def test_repeated_matching_with_insertions(self) -> None:
        rng = random.Random(0)
        for n1, n2 in [(0, 0), (0, 3), (3, 0), (1, 1), (3, 5), (5, 3)]:
            solver = BipartiteMatching(n1, n2)
            reference = BipartiteMaximumMatching(n1, n2)
            edges: set[tuple[int, int]] = set()
            for _ in range(25):
                if n1 and n2:
                    u, v = rng.randrange(n1), rng.randrange(n2)
                    solver.add_edge(Node(u), Node(v))
                    reference.add_edge(u, v)
                    edges.add((u, v))
                expected = reference.solve().weight
                for _ in range(2):
                    result = solver.solve()
                    self.assertEqual(result.weight, expected)
                    self.assertEqual(result.weight, len(result.edges))
                    self.assertEqual(len({u for u, _ in result.edges}), expected)
                    self.assertEqual(len({v for _, v in result.edges}), expected)
                    self.assertTrue(set(result.edges) <= edges)

    def test_matching_validation_and_empty_success(self) -> None:
        for n1, n2 in [(-1, 2), (2, -1)]:
            with self.assertRaises(ValueError):
                BipartiteMatching(n1, n2)
        solver = BipartiteMatching(1, 1)
        for u, v in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
            with self.assertRaises(IndexError):
                solver.add_edge(Node(u), Node(v))
        result = solver.solve()
        self.assertEqual(result, MatchingSuccess(0, [], True))
        self.assertTrue(result.success)
        self.assertFalse(bool(result))

    def test_diameter_weight_domain(self) -> None:
        tree = Tree(3)
        tree.add_edge(Node(0), Node(1), Weight(-10))
        tree.add_edge(Node(1), Node(2), Weight(5))
        with self.assertRaises(ValueError):
            tree_diameter(tree)
        tree = Tree(3)
        tree.add_edge(Node(0), Node(1), Weight(0))
        tree.add_edge(Node(1), Node(2), Weight(5))
        self.assertEqual(tree_diameter(tree).distance, 5)
        self.assertEqual(tree_diameter(Tree(1)).distance, 0)


if __name__ == '__main__':
    unittest.main()
