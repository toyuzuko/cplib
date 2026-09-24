import itertools
import random
import unittest

from cplib.graph.base import Capacity, Cost, Node, Weight
from cplib.graph.core import Graph, Tree
from cplib.graph.flow import MinimumCostBFlow
from cplib.graph.matching import BipartiteMaximumWeightMatching, BipartiteMinimumWeightMaximumMatching, MatchingSuccess
from cplib.graph.optimization import minimum_steiner_tree
from cplib.graph.scheduling import optimal_scheduling_on_dag
from cplib.graph.spanning import minimum_diameter_spanning_tree
from cplib.graph.treedp import rerooting_dp


class GraphOptimizationBugsTest(unittest.TestCase):
    def test_sparse_weighted_matching_against_enumeration(self) -> None:
        rng = random.Random(0)
        for cls in (BipartiteMinimumWeightMaximumMatching, BipartiteMaximumWeightMatching):
            maximize = cls is BipartiteMaximumWeightMatching
            for case in range(150):
                n, m = (2, 2) if case == 0 else (rng.randrange(1, 5), rng.randrange(1, 5))
                solver = cls(n, m)
                costs: dict[tuple[int, int], int] = {}
                if case == 0:
                    edges = [(0, 0, 10 if maximize else 0), (0, 1, 0 if maximize else 10), (1, 0, 0 if maximize else 10)]
                else:
                    scale = 10**100 if case % 7 == 0 else 1
                    edges = [(rng.randrange(n), rng.randrange(m), rng.randrange(0 if maximize else -10, 11) * scale) for _ in range(rng.randrange(2 * n * m + 1))]
                for u, v, w in edges:
                    solver.add_edge(u, v, w)
                    old = costs.get((u, v), w)
                    costs[u, v] = max(old, w) if maximize else min(old, w)
                best = (0, 0)
                for assignment in itertools.product(range(-1, m), repeat=n):
                    pairs = [(u, v) for u, v in enumerate(assignment) if v != -1]
                    if len({v for _, v in pairs}) != len(pairs) or any(pair not in costs for pair in pairs):
                        continue
                    weight = sum(costs[pair] for pair in pairs)
                    best = max(best, (len(pairs), weight if maximize else -weight))
                result = solver.solve()
                self.assertIsInstance(result, MatchingSuccess)
                self.assertIs(result.success, True)
                self.assertEqual((len(result.edges), result.weight if maximize else -result.weight), best)
                self.assertEqual(sum(costs[pair] for pair in result.edges), result.weight)
                self.assertEqual(len({u for u, _ in result.edges}), len(result.edges))
                self.assertEqual(len({v for _, v in result.edges}), len(result.edges))
                self.assertEqual(solver.solve(), result)
        for cls in (BipartiteMinimumWeightMaximumMatching, BipartiteMaximumWeightMatching):
            for n, m in ((0, 0), (0, 3), (3, 0), (2, 3)):
                solver = cls(n, m)
                for _ in range(2):
                    result = solver.solve()
                    self.assertIsInstance(result, MatchingSuccess)
                    self.assertIs(result.success, True)
                    self.assertEqual(result.weight, 0)
                    self.assertEqual(result.edges, [])
                if n and m:
                    solver.add_edge(1, 2, 0)
                    self.assertEqual(solver.solve(), MatchingSuccess(0, [(1, 2)], True))

    def test_steiner_tree_against_edge_subsets(self) -> None:
        rng = random.Random(0)
        for case in range(160):
            n = 3 if case == 0 else rng.randrange(2, 7)
            graph = Graph(n)
            for v in range(1, n):
                graph.add_edge(Node(v - 1 if case == 0 else rng.randrange(v)), Node(v), Weight(0 if case == 0 else rng.randrange(4)))
            if case:
                for _ in range(rng.randrange(4)):
                    graph.add_edge(Node(rng.randrange(n)), Node(rng.randrange(n)), Weight(rng.randrange(4)))
            terminals = list(map(Node, range(n))) if case == 0 else rng.sample(list(map(Node, range(n))), rng.randrange(1, n + 1))
            best = sum(graph.wt) + 1
            for mask in range(1 << graph.m):
                adjacency: list[list[int]] = [[] for _ in range(n)]
                cost = 0
                for e, (u, v) in enumerate(graph.edges):
                    if mask >> e & 1:
                        adjacency[u].append(v)
                        adjacency[v].append(u)
                        cost += graph.wt[e]
                reached = {terminals[0]}
                stack = [terminals[0]]
                while stack:
                    for v in adjacency[stack.pop()]:
                        if v not in reached:
                            reached.add(v)
                            stack.append(v)
                if all(t in reached for t in terminals):
                    best = min(best, cost)
            result = minimum_steiner_tree(graph, terminals)
            self.assertEqual(result.weight, best)
            self.assertEqual(len(result.edges), len(set(result.edges)))
            self.assertEqual(sum(graph.wt[e] for e in result.edges), best)
            components = [{v} for v in range(n)]
            for e in result.edges:
                u, v = graph.edges[e]
                left = next(c for c in components if u in c)
                right = next(c for c in components if v in c)
                self.assertIsNot(left, right, 'Reconstructed edges contain a cycle')
                components.remove(right)
                left.update(right)
            self.assertTrue(any(set(terminals) <= component for component in components))

    def test_dag_scheduling_large_and_signed_costs(self) -> None:
        graph = Graph(2, is_directed=True)
        self.assertEqual(optimal_scheduling_on_dag(graph, [10**9] * 2, [10**9] * 2)[0], 3 * 10**18)
        self.assertEqual(optimal_scheduling_on_dag(Graph(1, is_directed=True), [1], [1 << 60]), (1 << 60, [0]))
        self.assertEqual(optimal_scheduling_on_dag(Graph(0, is_directed=True), [], []), (0, []))
        rng = random.Random(0)
        for _ in range(80):
            n = rng.randrange(1, 7)
            graph = Graph(n, is_directed=True)
            for u in range(n):
                for v in range(u + 1, n):
                    if rng.randrange(3) == 0:
                        graph.add_edge(Node(u), Node(v))
            duration = [rng.randrange(5) * 10**20 for _ in range(n)]
            weight = [rng.randrange(-3, 5) for _ in range(n)]
            candidates: list[int] = []
            for order in itertools.permutations(range(n)):
                if any(order.index(u) > order.index(v) for u, v in graph.edges):
                    continue
                time = cost = 0
                for v in order:
                    time += duration[v]
                    cost += time * weight[v]
                candidates.append(cost)
            cost, order = optimal_scheduling_on_dag(graph, duration, weight)
            self.assertEqual(cost, min(candidates))
            self.assertEqual(sorted(order), list(range(n)))
            self.assertTrue(all(order.index(u) < order.index(v) for u, v in graph.edges))
            self.assertEqual(sum(weight[v] * sum(duration[u] for u in order[:i + 1]) for i, v in enumerate(order)), cost)

    def test_b_flow_repeated_solves_and_changed_inputs(self) -> None:
        solver = MinimumCostBFlow(2)
        solver.add_edge(Node(0), Node(1), Capacity(1), Capacity(2), Cost(1))
        solver.add_excess(Node(0), Capacity(1))
        solver.add_excess(Node(1), Capacity(-1))
        first = solver.solve()
        self.assertTrue(first.feasible)
        self.assertEqual(first.cost, 1)
        self.assertEqual(solver.solve(), first)
        self.assertEqual(solver.excess, [1, -1])
        solver.add_excess(Node(0), Capacity(2))
        solver.add_excess(Node(1), Capacity(-2))
        self.assertFalse(solver.solve().feasible)
        self.assertFalse(solver.solve().feasible)
        solver.add_edge(Node(0), Node(1), Capacity(0), Capacity(3), Cost(-1))
        self.assertEqual(solver.solve().cost, -1)
        self.assertEqual(solver.solve().cost, -1)
        self.assertEqual(first.edges[0].flow, 1)
        invalid = MinimumCostBFlow(2)
        invalid.add_edge(Node(0), Node(1), Capacity(2), Capacity(1), Cost(0))
        for _ in range(2):
            result = invalid.solve()
            self.assertFalse(result.feasible)
            self.assertEqual(result.cost, 0)
            self.assertEqual(result.edges[0].flow, 0)

    def test_b_flow_against_enumeration(self) -> None:
        rng = random.Random(0)
        for _ in range(160):
            n = rng.randrange(1, 5)
            solver = MinimumCostBFlow(n)
            bounds: list[range] = []
            supply = [0] * n
            for _ in range(rng.randrange(7)):
                u, v = rng.randrange(n), rng.randrange(n)
                lower = rng.randrange(-2, 2)
                upper = rng.randrange(lower, 3)
                solver.add_edge(Node(u), Node(v), Capacity(lower), Capacity(upper), Cost(rng.randrange(-3, 4)))
                bounds.append(range(lower, upper + 1))
                chosen = rng.randrange(lower, upper + 1)
                supply[u] += chosen
                supply[v] -= chosen
            if rng.randrange(3) == 0:
                supply[rng.randrange(n)] += 1
                supply[rng.randrange(n)] -= 1
            for v, value in enumerate(supply):
                solver.add_excess(Node(v), Capacity(value))
            best: int | None = None
            for flows in itertools.product(*bounds):
                balance = [0] * n
                cost = 0
                for flow, (u, v, _, _, price) in zip(flows, solver.edges):
                    balance[u] += flow
                    balance[v] -= flow
                    cost += flow * price
                if balance == supply and (best is None or cost < best):
                    best = cost
            for _ in range(2):
                result = solver.solve()
                self.assertEqual(result.feasible, best is not None)
                self.assertEqual(solver.excess, supply)
                if best is None:
                    continue
                self.assertEqual(result.cost, best)
                balance = [0] * n
                for edge in result.edges:
                    self.assertLessEqual(edge.lower, edge.flow)
                    self.assertLessEqual(edge.flow, edge.upper)
                    balance[edge.source] += edge.flow
                    balance[edge.target] -= edge.flow
                self.assertEqual(balance, supply)
                self.assertEqual(sum(edge.flow * edge.cost for edge in result.edges), best)

    def test_minimum_diameter_rejects_negative_edges(self) -> None:
        for n in (1, 2):
            graph = Graph(n)
            graph.add_edge(Node(0), Node(n - 1), Weight(-1))
            with self.assertRaisesRegex(ValueError, 'negative'):
                minimum_diameter_spanning_tree(graph)
        graph = Graph(3)
        graph.add_edge(Node(0), Node(1), Weight(0))
        graph.add_edge(Node(1), Node(2), Weight(0))
        self.assertEqual(minimum_diameter_spanning_tree(graph).diameter, 0)

    def test_rerooting_preserves_neighbor_order(self) -> None:
        rng = random.Random(0)
        for _ in range(50):
            n = rng.randrange(1, 12)
            edges = [(rng.randrange(v), v) for v in range(1, n)]
            rng.shuffle(edges)
            tree = Tree(n)
            for u, v in edges:
                tree.add_edge(Node(u), Node(v))
            expected: list[str] = []
            for root in range(n):
                parent = [-1] * n
                order = [root]
                for v in order:
                    for u, _ in tree.tree[v]:
                        if u != parent[v]:
                            parent[u] = v
                            order.append(u)
                values = [''] * n
                for v in reversed(order):
                    values[v] = f'({v}' + ''.join(f'[{e}{values[u]}]' for u, e in tree.tree[v] if u != parent[v]) + ')'
                expected.append(values[root])
            for root in range(n):
                tree.build(Node(root))
                actual = rerooting_dp(tree, '', lambda a, b: a + b, lambda value, e: f'[{e}{value}]', lambda value, v: f'({v}{value})')
                self.assertEqual(actual, expected)
        tree = Tree(5000)
        for v in range(1, tree.n):
            tree.add_edge(Node(v - 1), Node(v))
        tree.build(Node(0))
        self.assertEqual(rerooting_dp(tree, 0, max, lambda value, _e: value + 1, lambda value, _v: value), [max(v, tree.n - 1 - v) for v in range(tree.n)])


if __name__ == '__main__':
    unittest.main()
