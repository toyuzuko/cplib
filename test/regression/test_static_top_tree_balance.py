import random
import unittest
from operator import add

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.toptree import StaticTopTree, StaticTopTreeWithEdges


MOD = 998244353
Point = tuple[int, int]
Path = tuple[int, int, int, int]


def vertex_cluster(point: Point, value: int) -> Path:
    return 1, 0, (point[0] + value) % MOD, point[1] + 1


def edge_cluster(point: Point, edge: Point) -> Path:
    a, b = edge
    return a, b, (a * point[0] + b * point[1]) % MOD, point[1]


def compress(upper: Path, lower: Path) -> Path:
    a, b, total, size = upper
    c, d, subtotal, subsize = lower
    return a * c % MOD, (a * d + b) % MOD, (a * subtotal + b * subsize + total) % MOD, size + subsize


def rake(left: Point, right: Point) -> Point:
    return (left[0] + right[0]) % MOD, left[1] + right[1]


class StaticTopTreeBalanceTest(unittest.TestCase):
    def test_affine_dp_updates_and_all_subtrees(self) -> None:
        for seed in range(10):
            rng = random.Random(seed)
            n = 1 if seed == 0 else 35
            tree = Tree(n)
            for v in range(1, n):
                tree.add_edge(Node(v), Node(rng.randrange(v)))
            tree.build(Node(rng.randrange(n)))
            values = [rng.randrange(MOD) for _ in range(n)]
            edges = [(rng.randrange(MOD), rng.randrange(MOD)) for _ in range(n - 1)]
            top = StaticTopTreeWithEdges(tree, values, edges, (0, 0), vertex_cluster, edge_cluster, lambda path: (path[2], path[3]), rake, compress)
            for step in range(120):
                if n > 1 and rng.randrange(2):
                    edge_id = rng.randrange(n - 1)
                    edges[edge_id] = rng.randrange(MOD), rng.randrange(MOD)
                    top.set_edge(edge_id, edges[edge_id])
                    self.assertEqual(top.get_edge(edge_id), edges[edge_id])
                else:
                    v = rng.randrange(n)
                    values[v] = rng.randrange(MOD)
                    top.set_vertex(v, values[v])
                    self.assertEqual(top.get_vertex(v), values[v])
                expected = values[:]
                sizes = [1] * n
                for v in reversed(tree.ord[1:]):
                    p = tree.par_v[v]
                    a, b = edges[tree.par_e[v]]
                    expected[p] = (expected[p] + a * expected[v] + b * sizes[v]) % MOD
                    sizes[p] += sizes[v]
                with self.subTest(seed=seed, step=step):
                    self.assertEqual(top.tree_value()[2], expected[tree.root])
                    for v in range(n):
                        result = top.subtree_value(v)
                        self.assertEqual((result[2], result[3]), (expected[v], sizes[v]))

    def test_nested_heavy_paths_have_logarithmic_update_depth(self) -> None:
        edges: list[tuple[int, int]] = []
        n = 1
        root = 0
        for _ in range(12):
            old_n = n
            new_root = n
            n += 1
            for i in range(old_n):
                edges.append((new_root if i == 0 else n - 1, n))
                n += 1
            edges.append((new_root, root))
            root = new_root
        tree = Tree(n)
        for u, v in edges:
            tree.add_edge(Node(u), Node(v))
        tree.build(Node(root))
        top = StaticTopTree(tree, [1] * n, 0, add, lambda path: path, add, add)
        # Point updates visit precisely the cluster ancestors of the vertex.
        max_depth = 0
        stack = [(top._root, 1)]
        while stack:
            node, depth = stack.pop()
            max_depth = max(max_depth, depth)
            for child in (top._left[node], top._right[node]):
                if child != -1:
                    stack.append((child, depth + 1))
        self.assertLessEqual(max_depth, 4 * n.bit_length())
        for value in (2, -10, 42):
            top.set(0, value)
            self.assertEqual(top.tree_value(), n - 1 + value)

    def test_noncommutative_rake_preserves_child_order(self) -> None:
        tree = Tree(9)
        # The long child is heavy. Light children have unequal subtree sizes.
        for u, v in [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (0, 7), (0, 8)]:
            tree.add_edge(Node(u), Node(v))
        tree.build(Node(0))
        top = StaticTopTree(tree, list('abcdefghi'), '', lambda point, value: value + point,
                            lambda path: path, add, add)
        self.assertEqual(top.tree_value(), 'afghibcde')
        top.set(6, 'X')
        self.assertEqual(top.tree_value(), 'afXhibcde')
        self.assertEqual(top.subtree_value(5), 'fX')


if __name__ == '__main__':
    unittest.main()
