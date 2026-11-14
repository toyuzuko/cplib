import unittest

from cplib.graph import Namori, Pseudoforest, Pseudotree
from cplib.graph import __all__ as graph_exports
from cplib.graph import families
from cplib.graph.base import Node, Weight
from cplib.graph.core import Graph


def _graph(n: int, edges: list[tuple[int, int, int]]) -> Graph:
    graph = Graph(n)
    for u, v, weight in edges:
        graph.add_edge(Node(u), Node(v), Weight(weight))
    return graph


class PseudoforestNamingTest(unittest.TestCase):
    def test_pseudotree_is_the_same_class_as_namori(self) -> None:
        self.assertIs(Pseudotree, Namori)
        self.assertIs(families.Pseudotree, Namori)
        self.assertIs(families.Pseudoforest, Pseudoforest)
        self.assertIn('Pseudoforest', graph_exports)
        self.assertIn('Pseudotree', graph_exports)
        graph = _graph(5, [(0, 1, 2), (1, 2, 3), (2, 0, 10), (1, 3, 4), (3, 4, 5)])
        tree = Pseudotree(graph)
        self.assertEqual(tree.cycle, [0, 1, 2])
        self.assertEqual(tree.cycle_root(4), 1)
        self.assertEqual(tree.weighted_path_length(4, 2), (12, 21))

    def test_pseudoforest_accepts_mixed_components(self) -> None:
        graph = _graph(8, [(0, 1, 2), (1, 2, 3), (2, 0, 10), (1, 3, 4), (4, 5, 5), (5, 6, 7)])
        forest = Pseudoforest(graph)
        self.assertEqual(len(forest.components), 3)
        self.assertTrue(forest.has_cycle(3))
        self.assertFalse(forest.has_cycle(4))
        self.assertFalse(forest.has_cycle(7))
        self.assertEqual(forest.component_cycle(4), [])
        self.assertEqual(forest.component_cycle(3), [0, 1, 2])
        self.assertEqual(forest.cycle_root(3), 1)
        self.assertEqual(forest.weighted_path_length(3, 2), (7, 16))
        self.assertEqual(forest.path_length(4, 6), (2, 2))
        self.assertEqual(forest.dist(4, 6), 12)
        self.assertEqual(forest.branch_lca(5, 6), 5)
        self.assertFalse(forest.same_component(0, 4))
        self.assertIsNone(forest.branch_lca(0, 4))
        with self.assertRaises(ValueError):
            forest.cycle_root(4)
        with self.assertRaises(ValueError):
            forest.hops(0, 4)

    def test_pseudotree_rejects_tree_and_disconnected_inputs(self) -> None:
        inputs = [
            Graph(0),
            Graph(1),
            _graph(3, [(0, 1, 1), (1, 2, 1)]),
            _graph(6, [(0, 1, 1), (1, 2, 1), (2, 0, 1), (3, 4, 1), (4, 5, 1), (5, 3, 1)]),
        ]
        for graph in inputs:
            with self.subTest(n=graph.n, m=graph.m):
                Pseudoforest(graph)
                with self.assertRaises(ValueError):
                    Pseudotree(graph)

    def test_pseudoforest_rejects_invalid_components(self) -> None:
        with self.assertRaisesRegex(ValueError, 'Pseudoforest requires an undirected graph'):
            Pseudoforest(Graph(3, is_directed=True))
        two_cycles = _graph(4, [(0, 1, 1), (1, 2, 1), (2, 0, 1), (1, 3, 1), (2, 3, 1)])
        with self.assertRaises(ValueError):
            Pseudoforest(two_cycles)


if __name__ == '__main__':
    unittest.main()
