import random
import unittest

from cplib.graph.connectivity import OfflineDynamicConnectivity, UndoableDSUWithLazyAggregate


MOD = 101
Tag = tuple[int, int]


def compose(f: Tag, g: Tag) -> Tag:
    return f[0] * g[0] % MOD, (f[0] * g[1] + f[1]) % MOD


def difference(f: Tag, g: Tag) -> Tag:
    inverse = pow(g[0], -1, MOD)
    return compose(f, (inverse, -g[1] * inverse % MOD))


def mapping(f: Tag, x: int) -> int:
    return (f[0] * x + f[1]) % MOD


def make_dsu(values: list[int]) -> UndoableDSUWithLazyAggregate[int, int, Tag]:
    return UndoableDSUWithLazyAggregate(values, lambda x, y: (x + y) % MOD, lambda x: -x % MOD, 0, mapping, lambda f, s, n: (f[0] * s + f[1] * n) % MOD, compose, difference, (1, 0), lambda x: x)


def make_offline(values: list[int], time_max: int) -> OfflineDynamicConnectivity[int, int, Tag]:
    return OfflineDynamicConnectivity(len(values), time_max, values, lambda x, y: (x + y) % MOD, lambda x: -x % MOD, 0, mapping, lambda f, s, n: (f[0] * s + f[1] * n) % MOD, compose, difference, (1, 0), lambda x: x, lambda new, old: (1, (new - old) % MOD))


class ConnectivityLazyUpdatesTest(unittest.TestCase):
    def test_affine_component_and_point_updates(self) -> None:
        dsu = make_dsu([1])
        dsu.component_apply(0, (2, 0))
        dsu.component_apply(0, (1, 3))
        self.assertEqual(dsu.vertex_get(0), 5)
        self.assertEqual(dsu.component_aggregate(0), 5)
        dsu = make_dsu([1])
        dsu.component_apply(0, (2, 0))
        dsu.vertex_apply(0, (3, 0))
        self.assertEqual(dsu.vertex_get(0), 6)
        self.assertEqual(dsu.component_aggregate(0), 6)

    def test_affine_merge_undo_and_rollback_against_naive(self) -> None:
        rng = random.Random(0)
        for _ in range(35):
            n = rng.randrange(1, 18)
            values = [rng.randrange(MOD) for _ in range(n)]
            dsu = make_dsu(values)
            groups = [{v} for v in range(n)]
            history: list[list[set[int]]] = []
            for step in range(350):
                a, b = rng.randrange(n), rng.randrange(n)
                action = rng.randrange(5)
                if action == 0:
                    history.append([group.copy() for group in groups])
                    left = next(group for group in groups if a in group)
                    right = next(group for group in groups if b in group)
                    self.assertEqual(dsu.merge(a, b), left is not right)
                    if left is not right:
                        groups.remove(right)
                        left.update(right)
                elif action == 1 and history:
                    dsu.undo()
                    groups = history.pop()
                elif action == 2 and history:
                    snapshot = rng.randrange(len(history) + 1)
                    dsu.rollback(snapshot)
                    while len(history) > snapshot:
                        groups = history.pop()
                elif action == 3:
                    f = rng.randrange(1, MOD), rng.randrange(MOD)
                    dsu.vertex_apply(a, f)
                    values[a] = mapping(f, values[a])
                else:
                    f = rng.randrange(1, MOD), rng.randrange(MOD)
                    dsu.component_apply(a, f)
                    for v in next(group for group in groups if a in group):
                        values[v] = mapping(f, values[v])
                self.assertEqual(dsu.snapshot(), len(history))
                for group in groups:
                    total = sum(values[v] for v in group) % MOD
                    for v in group:
                        self.assertEqual(dsu.vertex_get(v), values[v], (step, action, v))
                        self.assertEqual(dsu.component_aggregate(v), total, (step, action, v))
                        self.assertEqual(dsu.size(v), len(group))
                        self.assertEqual(dsu.same(a, v), a in group)

    def test_distinct_value_and_aggregate_types(self) -> None:
        def aggregate(f: Tag, value: tuple[int, int], n: int) -> tuple[int, int]:
            a, b = f
            total, squares = value
            return (a * total + b * n) % MOD, (a * a * squares + 2 * a * b * total + b * b * n) % MOD

        dsu = UndoableDSUWithLazyAggregate([1, 2, 3], lambda x, y: ((x[0] + y[0]) % MOD, (x[1] + y[1]) % MOD), lambda x: (-x[0] % MOD, -x[1] % MOD), (0, 0), mapping, aggregate, compose, difference, (1, 0), lambda x: (x, x * x % MOD))
        dsu.component_apply(0, (2, 1))
        dsu.component_apply(1, (3, 2))
        dsu.merge(0, 1)
        dsu.component_apply(1, (4, 5))
        dsu.vertex_apply(0, (2, 3))
        dsu.merge(2, 1)
        dsu.component_apply(2, (5, 7))
        expected = [mapping((5, 7), mapping((2, 3), mapping((4, 5), 3))), mapping((5, 7), mapping((4, 5), 8)), mapping((5, 7), 3)]
        self.assertEqual([dsu.vertex_get(v) for v in range(3)], expected)
        self.assertEqual(dsu.component_aggregate(0), (sum(expected) % MOD, sum(x * x for x in expected) % MOD))
        dsu.rollback(0)
        for v, x in enumerate(expected):
            self.assertEqual(dsu.component_aggregate(v), (x, x * x % MOD))

    def test_offline_initial_values_replay_and_result_order(self) -> None:
        values = [5, 7]
        dc = OfflineDynamicConnectivity(2, 3, values=values)
        values[0] = 100
        dc.insert_edge(0, 1, 0)
        dc.set_query_vertex_add(0, 1, 0)
        dc.set_query_component_sum(0, 2)
        dc.set_query_vertex_get(0, 0)
        dc.set_query_vertex_get(1, 0)
        for _ in range(3):
            self.assertEqual(dc.run(), [6, 7, 13])
            self.assertEqual(dc.edges, [])
        dc.erase_edge(0, 1, 1)
        self.assertEqual(dc.run(), [6, 7, 6])
        dc.set_query_vertex_set(0, 20, 1)
        self.assertEqual(dc.run(), [6, 7, 20])
        self.assertEqual(dc.run(), [6, 7, 20])
        self.assertEqual(len(dc.edges), 1)
        self.assertEqual(OfflineDynamicConnectivity(0, 0).run(), [])
        dc = OfflineDynamicConnectivity(1, 0, values=[9])
        dc.set_query_vertex_get(0, 0)
        self.assertEqual(dc.run(), [9])

    def test_invalid_offline_edges_preserve_events(self) -> None:
        dc = OfflineDynamicConnectivity(2, 5)
        dc.insert_edge(0, 1, 1)
        dc.set_query_is_same(0, 1, 0)
        dc.set_query_is_same(0, 1, 1)
        before = (dc.edges[:], dc.insert_times.copy(), dc.unerased_edges.copy())
        for operation in (lambda: dc.insert_edge(1, 0, 2), lambda: dc.erase_edge(0, 1, 0)):
            with self.assertRaises(ValueError):
                operation()
            self.assertEqual((dc.edges, dc.insert_times, dc.unerased_edges), before)
            self.assertEqual(dc.run(), [0, 1])
        dc.erase_edge(0, 1, 3)
        before = (dc.edges[:], dc.insert_times.copy(), dc.unerased_edges.copy())
        for operation in (lambda: dc.erase_edge(1, 0, 4), lambda: dc.insert_edge(0, 1, 2)):
            with self.assertRaises(ValueError):
                operation()
            self.assertEqual((dc.edges, dc.insert_times, dc.unerased_edges), before)
        dc.insert_edge(0, 1, 3)
        dc.erase_edge(0, 1, 3)
        dc.set_query_is_same(0, 1, 3)
        self.assertEqual(dc.run(), [0, 1, 0])
        for n, last, values in [(-1, 0, None), (0, -1, None), (2, 1, [1]), (1, 1, [1, 2])]:
            with self.assertRaises(ValueError):
                OfflineDynamicConnectivity(n, last, values=values)

    def test_offline_affine_updates_against_naive(self) -> None:
        rng = random.Random(0)
        for _ in range(70):
            n = rng.randrange(2, 10)
            values = [rng.randrange(MOD) for _ in range(n)]
            dc = make_offline(values, 49)
            edges: set[tuple[int, int]] = set()
            expected: list[int] = []
            for time in range(50):
                u, v = sorted(rng.sample(range(n), 2))
                if (u, v) in edges:
                    edges.remove((u, v))
                    dc.erase_edge(u, v, time)
                else:
                    edges.add((u, v))
                    dc.insert_edge(u, v, time)
                component = {u}
                stack = [u]
                while stack:
                    x = stack.pop()
                    for a, b in edges:
                        y = b if a == x else a if b == x else -1
                        if y != -1 and y not in component:
                            component.add(y)
                            stack.append(y)
                f = rng.randrange(1, MOD), rng.randrange(MOD)
                dc.set_query_component_apply(u, f, time)
                for x in component:
                    values[x] = mapping(f, values[x])
                f = rng.randrange(1, MOD), rng.randrange(MOD)
                dc.set_query_vertex_apply(v, f, time)
                values[v] = mapping(f, values[v])
                if time % 7 == 0:
                    value = rng.randrange(MOD)
                    dc.set_query_vertex_set(u, value, time)
                    values[u] = value
                dc.set_query_component_aggregate(u, time)
                dc.set_query_vertex_get(v, time)
                dc.set_query_is_same(u, v, time)
                expected.extend((sum(values[x] for x in component) % MOD, values[v], int(v in component)))
            self.assertEqual(dc.run(), expected)
            self.assertEqual(dc.run(), expected)


if __name__ == '__main__':
    unittest.main()
