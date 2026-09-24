from collections import Counter
import itertools
import random
import unittest

from cplib.graph.base import Node, Weight
from cplib.graph.core import Graph
from cplib.graph.counting import chromatic_polynomial, count_spanning_trees, induced_subgraph
from cplib.graph.optimization import traveling_salesman_problem
from cplib.graph.shortest import bellman_ford, dijkstra, dijkstra_with_prev, radix_dijkstra, simplify_graph, update_dist_matrix, warshall_floyd
from cplib.mathematics.convolution import ConvolutionMod
from cplib.mathematics.polynomial import FormalPowerSeriesMod


class GraphPathsAndCountingTest(unittest.TestCase):
    def test_induced_subgraph_preserves_logical_edges(self) -> None:
        rng = random.Random(0)
        for directed in (False, True):
            for _ in range(80):
                n = rng.randrange(1, 9)
                graph = Graph(n, is_directed=directed)
                for _ in range(rng.randrange(30)):
                    graph.add_edge(Node(rng.randrange(n)), Node(rng.randrange(n)), Weight(rng.randrange(-5, 6)))
                vertices = rng.sample(list(map(Node, range(n))), rng.randrange(n + 1))
                mapping = {v: i for i, v in enumerate(vertices)}
                expected: Counter[tuple[int, int, int]] = Counter()
                for (u, v), w in zip(graph.edges, graph.wt):
                    if u in mapping and v in mapping:
                        a, b = mapping[u], mapping[v]
                        if not directed:
                            a, b = sorted((a, b))
                        expected[a, b, w] += 1
                result = induced_subgraph(graph, vertices)
                actual: Counter[tuple[int, int, int]] = Counter()
                for (u, v), w in zip(result.edges, result.wt):
                    a, b = (u, v) if directed else sorted((u, v))
                    actual[a, b, w] += 1
                self.assertEqual(actual, expected)
                self.assertEqual(result.n, len(vertices))
                self.assertEqual(sum(map(len, result.graph)), result.m * (1 if directed else 2))
        graph = Graph(2)
        graph.add_edge(Node(0), Node(1))
        self.assertEqual(count_spanning_trees(induced_subgraph(graph, [Node(0), Node(1)])), 1)

    def test_tsp_weight_and_forward_tour_against_permutations(self) -> None:
        rng = random.Random(0)
        for directed in (False, True):
            for _ in range(100):
                n = rng.randrange(1, 8)
                graph = Graph(n, is_directed=directed)
                costs: dict[tuple[int, int], int] = {}
                for _ in range(rng.randrange(n * n * 2 + 1)):
                    u, v, w = rng.randrange(n), rng.randrange(n), rng.randrange(-5, 11)
                    graph.add_edge(Node(u), Node(v), Weight(w))
                    costs[u, v] = min(costs.get((u, v), w), w)
                    if not directed:
                        costs[v, u] = costs[u, v]
                optimum: int | None = 0 if n == 1 else None
                for perm in itertools.permutations(range(1, n)):
                    if n == 1:
                        continue
                    tour = (0,) + perm + (0,)
                    arcs = list(zip(tour, tour[1:]))
                    if all(arc in costs for arc in arcs):
                        cost = sum(costs[arc] for arc in arcs)
                        optimum = cost if optimum is None else min(optimum, cost)
                if optimum is None:
                    with self.assertRaises(ValueError):
                        traveling_salesman_problem(graph)
                else:
                    result = traveling_salesman_problem(graph)
                    self.assertEqual(result.weight, optimum)
                    self.assertEqual(result.path[0], 0)
                    self.assertEqual(sorted(result.path), list(range(n)))
                    if n > 1:
                        tour = result.path + [Node(0)]
                        self.assertEqual(sum(costs[u, v] for u, v in zip(tour, tour[1:])), optimum)
        graph = Graph(3, is_directed=True)
        for u in range(3):
            graph.add_edge(Node(u), Node((u + 1) % 3), Weight(1))
        self.assertEqual(traveling_salesman_problem(graph).path, [0, 1, 2])
        with self.assertRaises(ValueError):
            traveling_salesman_problem(Graph(0))

    def test_floyd_negative_cycle_propagation(self) -> None:
        graph = Graph(2, is_directed=True)
        for u, v, w in [(0, 1, 3), (1, 0, 3), (1, 1, -1)]:
            graph.add_edge(Node(u), Node(v), Weight(w))
        self.assertEqual(warshall_floyd(graph), [[-Graph.dst_inf] * 2 for _ in range(2)])
        rng = random.Random(0)
        for _ in range(500):
            n = rng.randrange(1, 8)
            graph = Graph(n, is_directed=bool(rng.randrange(2)))
            for _ in range(rng.randrange(n * n + 1)):
                graph.add_edge(Node(rng.randrange(n)), Node(rng.randrange(n)), Weight(rng.randrange(-4, 8)))
            self.assertEqual(warshall_floyd(graph), [bellman_ford(graph, Node(v)) for v in range(n)])

    def test_distance_matrix_updates_and_atomic_rejection(self) -> None:
        rng = random.Random(0)
        for directed in (False, True):
            for _ in range(70):
                n = rng.randrange(1, 8)
                potential = [rng.randrange(-8, 9) if directed else 0 for _ in range(n)]
                graph = Graph(n, is_directed=directed)
                matrix = warshall_floyd(graph)
                for _ in range(12):
                    u, v = rng.randrange(n), rng.randrange(n)
                    w = Weight(rng.randrange(7) + potential[v] - potential[u])
                    update_dist_matrix(matrix, Node(u), Node(v), w, directed)
                    graph.add_edge(Node(u), Node(v), w)
                    self.assertEqual(matrix, warshall_floyd(graph))
        cases = [([[0, 1], [Graph.dst_inf, 0]], 1, 0, -2, True), ([[0, Graph.dst_inf], [Graph.dst_inf, 0]], 0, 1, -1, False), ([[0]], 0, 0, -1, True), ([[-Graph.dst_inf]], 0, 0, 1, True), ([[0]], 0, 0, Graph.dst_inf, True)]
        for matrix, u, v, w, directed in cases:
            before = [row[:] for row in matrix]
            with self.assertRaises(ValueError):
                update_dist_matrix(matrix, Node(u), Node(v), Weight(w), directed)
            self.assertEqual(matrix, before)

    def test_simplification_large_weights_and_dijkstra_validation(self) -> None:
        for directed in (False, True):
            graph = Graph(3, is_directed=directed)
            graph.add_edge(Node(0), Node(1), Weight(Graph.dst_inf))
            graph.add_edge(Node(1), Node(2), Weight(10**100))
            graph.add_edge(Node(1), Node(2), Weight(10**101))
            graph.add_edge(Node(1), Node(1), Weight(-1))
            result = simplify_graph(graph)
            self.assertEqual(result.edges, [(0, 1), (1, 2)])
            self.assertEqual(result.wt, [Graph.dst_inf, 10**100])
        graph = Graph(2)
        graph.add_edge(Node(0), Node(1), Weight(-1))
        for solve in (dijkstra, dijkstra_with_prev):
            with self.assertRaisesRegex(ValueError, 'negative'):
                solve(graph, Node(0))
        graph = Graph(3, is_directed=True)
        graph.add_edge(Node(0), Node(1), Weight(Graph.dst_inf - 2))
        graph.add_edge(Node(1), Node(2), Weight(1))
        for solve in (dijkstra, radix_dijkstra, bellman_ford):
            self.assertEqual(solve(graph, Node(0)), [0, Graph.dst_inf - 2, Graph.dst_inf - 1])

    def test_chromatic_polynomial_small_primes_and_invalid_moduli(self) -> None:
        original = FormalPowerSeriesMod.get_mod()
        try:
            rng = random.Random(0)
            for n, mod in [(0, 2), (1, 2), (2, 3), (3, 5), (4, 5), (5, 7)]:
                for _ in range(12):
                    graph = Graph(n)
                    for u in range(n):
                        for v in range(u + 1, n):
                            if rng.randrange(2):
                                graph.add_edge(Node(u), Node(v))
                    coef = chromatic_polynomial(graph, mod).coef
                    self.assertEqual(len(coef), n + 1)
                    for colors in range(n + 1):
                        expected = sum(all(assignment[u] != assignment[v] for u, v in graph.edges) for assignment in itertools.product(range(colors), repeat=n))
                        actual = sum(c * pow(colors, i, mod) for i, c in enumerate(coef)) % mod
                        self.assertEqual(actual, expected % mod)
            for mod in (-1, 0, 1, 2, 4, 9):
                before = FormalPowerSeriesMod.get_mod()
                with self.assertRaisesRegex(ValueError, 'prime'):
                    chromatic_polynomial(Graph(2), mod)
                self.assertEqual(FormalPowerSeriesMod.get_mod(), before)
            graph = Graph(1)
            graph.add_edge(Node(0), Node(0))
            self.assertEqual(chromatic_polynomial(graph, 2).coef, [0, 0])
        finally:
            FormalPowerSeriesMod.set_mod(original)

    def test_convolution_at_small_transform_limits(self) -> None:
        original = ConvolutionMod.get_mod()
        try:
            for mod in (2, 3, 5, 7, 17, 998244353):
                ConvolutionMod.set_mod(mod)
                limit = min(8, (mod - 1) & -(mod - 1))
                for n in range(1, limit + 1):
                    for m in range(1, limit + 2 - n):
                        left, right = list(range(1, n + 1)), list(range(1, m + 1))
                        expected = [0] * (n + m - 1)
                        for i, a in enumerate(left):
                            for j, b in enumerate(right):
                                expected[i + j] = (expected[i + j] + a * b) % mod
                        self.assertEqual(ConvolutionMod.convolution(left, right), expected)
            ConvolutionMod.set_mod(3)
            with self.assertRaises(ValueError):
                ConvolutionMod.convolution([1, 1], [1, 1])
        finally:
            ConvolutionMod.set_mod(original)


if __name__ == '__main__':
    unittest.main()
