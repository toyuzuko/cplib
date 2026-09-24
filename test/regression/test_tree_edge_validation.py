import unittest

from cplib.graph.base import Node, Weight
from cplib.graph.core import Tree
from cplib.graph.treedecomp import LinearTimeLCA, SparseTableLCA
from cplib.graph.scheduling import optimal_scheduling_on_tree
from cplib.graph.treedecomp import HeavyLightDecomposition
from cplib.graph.treedp import rerooting_dp


class TreeEdgeValidationTest(unittest.TestCase):
    def test_unbuilt_tree_raises_value_error(self) -> None:
        tree = Tree(2)
        for cls in (HeavyLightDecomposition, SparseTableLCA, LinearTimeLCA):
            with self.subTest(cls=cls.__name__):
                with self.assertRaises(ValueError):
                    cls(tree)
        with self.assertRaises(ValueError):
            rerooting_dp(tree, 0, max, lambda value, edge: value + 1, lambda value, vertex: value)
        with self.assertRaises(ValueError):
            optimal_scheduling_on_tree(tree, [1, 1], [1, 1])

    def test_invalid_edge_count_does_not_build_tree(self) -> None:
        tree = Tree(2)
        with self.assertRaises(ValueError):
            tree.build(Node(0))
        self.assertEqual(tree.root, -1)
        tree.add_edge(Node(0), Node(1))
        tree.build(Node(0))
        self.assertEqual(tree.par_v, [-1, 0])

    def test_rejected_edges_leave_the_tree_usable(self) -> None:
        tree = Tree(4, connectivity_check=True)
        tree.add_edge(Node(0), Node(1))
        tree.add_edge(Node(1), Node(2))
        before = ([row[:] for row in tree.tree], tree.edges[:], tree.wt[:], tree.m, tree.is_weighted)
        for u, v in [(0, 1), (1, 0), (0, 2), (3, 3)]:
            with self.subTest(u=u, v=v):
                with self.assertRaises(ValueError):
                    tree.add_edge(Node(u), Node(v), Weight(7))
                self.assertEqual((tree.tree, tree.edges, tree.wt, tree.m, tree.is_weighted), before)
        tree.add_edge(Node(2), Node(3))
        tree.build(Node(0))
        self.assertEqual(tree.m, 3)
        self.assertEqual(tree.par_v, [-1, 0, 1, 2])
        self.assertEqual(tree.par_e, [-1, 0, 1, 2])
        self.assertEqual(tree.size, [4, 3, 2, 1])


if __name__ == '__main__':
    unittest.main()
