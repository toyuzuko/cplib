import random
import unittest

from cplib.datastructure.dsu import (
    DisjointSetUnion, WeightedDSU, DSUWithPotential, PartiallyPersistentDSU,
    UndoableDSU, RangeParallelDSU, QueryDSU, DSUOnlyPathHalving,
)


def merged(labels: list[int], a: int, b: int) -> list[int]:
    x, y = labels[a], labels[b]
    return [x if value == y else value for value in labels]


class DSUContractsTest(unittest.TestCase):
    def test_full_path_compression_and_sets(self) -> None:
        n = 64
        tree = DisjointSetUnion(n)
        for size in (1, 2, 4, 8, 16, 32):
            for start in range(0, n, 2 * size):
                tree.merge(start, start + size)
        path = []
        v = n - 1
        while tree.par_size[v] >= 0:
            path.append(v)
            v = tree.par_size[v]
        self.assertGreater(len(path), 2)
        self.assertEqual(tree.leader(n - 1), v)
        self.assertTrue(all(tree.par_size[x] == v for x in path))
        rng = random.Random(0)
        tree = DisjointSetUnion(n)
        labels = list(range(n))
        for _ in range(500):
            a, b = rng.randrange(n), rng.randrange(n)
            self.assertEqual(tree.merge(a, b), labels[a] != labels[b])
            labels = merged(labels, a, b)
            self.assertEqual(tree.size(a), labels.count(labels[a]))
            groups = sorted(sorted(i for i in range(n) if labels[i] == key) for key in set(labels))
            self.assertEqual(sorted(tree.groups()), groups)
            self.assertEqual(tree.roots(), [i for i in range(n) if tree.is_root(i)])

    def test_potential_groups_and_contradictions(self) -> None:
        def compose(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(a[b[i]] for i in range(4))

        def inverse(a: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(a.index(i) for i in range(4))

        n = 40
        rng = random.Random(0)
        values = [tuple(rng.sample(range(4), 4)) for _ in range(n)]
        numbers = [rng.randrange(-10**30, 10**30) for _ in range(n)]
        group = DSUWithPotential(n, compose, inverse, (0, 1, 2, 3))
        weighted = WeightedDSU(n)
        labels = list(range(n))
        for _ in range(1500):
            a, b = rng.randrange(n), rng.randrange(n)
            relation = compose(inverse(values[b]), values[a])
            self.assertEqual(group.merge(a, b, relation), labels[a] != labels[b])
            self.assertEqual(weighted.merge(a, b, numbers[b] - numbers[a]), labels[a] != labels[b])
            labels = merged(labels, a, b)
            x, y = rng.randrange(n), rng.randrange(n)
            for tree in (group, weighted):
                self.assertEqual(tree.same(x, y), labels[x] == labels[y])
                self.assertEqual(tree.size(x), labels.count(labels[x]))
            if labels[x] == labels[y]:
                expected = compose(inverse(values[y]), values[x])
                self.assertEqual(group.diff(x, y), expected)
                self.assertEqual(weighted.diff(x, y), numbers[y] - numbers[x])
                self.assertEqual(weighted.weight(y) - weighted.weight(x), numbers[y] - numbers[x])
                wrong = compose(expected, (1, 0, 2, 3))
                with self.assertRaises(ValueError):
                    group.merge(x, y, wrong)
                with self.assertRaises(ValueError):
                    weighted.merge(x, y, numbers[y] - numbers[x] + 1)
                self.assertEqual(group.diff(x, y), expected)
            else:
                for tree in (group, weighted):
                    with self.assertRaises(ValueError):
                        tree.diff(x, y)

    def test_partial_history(self) -> None:
        n = 20
        rng = random.Random(0)
        tree = PartiallyPersistentDSU(n)
        states = [list(range(n))]
        for _ in range(1000):
            a, b = rng.randrange(n), rng.randrange(n)
            current = states[-1]
            self.assertEqual(tree.merge(a, b), current[a] != current[b])
            states.append(merged(current, a, b))
            self.assertEqual(tree.t, len(states) - 2)
            for t in (-1, tree.t, rng.randrange(-1, tree.t + 1)):
                values = states[t + 1]
                x, y = rng.randrange(n), rng.randrange(n)
                self.assertEqual(tree.same(x, y, t), values[x] == values[y])
                self.assertEqual(tree.size(x, t), values.count(values[x]))
                root = tree.leader(x, t)
                self.assertEqual(values[root], values[x])
        self.assertLessEqual(sum(map(len, tree._size_history)), 2 * n - 1)
        before = tree.t, tree.par_size[:], [h[:] for h in tree._size_history]
        for a, b in ((-1, 0), (0, n)):
            with self.assertRaises(AssertionError):
                tree.merge(a, b)
            self.assertEqual((tree.t, tree.par_size, tree._size_history), before)
        for t in (-2, tree.t + 1, 1 << 100):
            with self.assertRaises(AssertionError):
                tree.leader(0, t)
            with self.assertRaises(AssertionError):
                tree.size(0, t)

    def test_undo_and_rollback(self) -> None:
        n = 15
        rng = random.Random(0)
        tree = UndoableDSU(n)
        states = [list(range(n))]
        for step in range(1200):
            action = rng.randrange(4)
            if action <= 1:
                a, b = rng.randrange(n), rng.randrange(n)
                self.assertEqual(tree.merge(a, b), states[-1][a] != states[-1][b])
                states.append(merged(states[-1], a, b))
            elif action == 2 and len(states) > 1:
                tree.undo()
                states.pop()
            elif action == 3:
                keep = rng.randrange(len(states))
                tree.rollback(2 * keep)
                states = states[:keep + 1]
            self.assertEqual(tree.snapshot(), 2 * (len(states) - 1))
            a, b = rng.randrange(n), rng.randrange(n)
            self.assertEqual(tree.same(a, b), states[-1][a] == states[-1][b])
            self.assertEqual(tree.size(a), states[-1].count(states[-1][a]))
            before = tree.par_size[:], tree.his[:]
            for snap in (-1, tree.snapshot() + 1, 1):
                with self.assertRaises(ValueError):
                    tree.rollback(snap)
                self.assertEqual((tree.par_size, tree.his), before)
        tree.rollback(0)
        with self.assertRaises(ValueError):
            tree.undo()

    def test_query_dsu_deep_and_branching(self) -> None:
        n = 5000
        values = list(range(n, 0, -1))
        tree = QueryDSU(n, lambda i: values[i], min)
        for i in range(n - 1):
            tree.link(i, i + 1)
        self.assertEqual(tree.eval(0), n - 1)
        self.assertEqual(tree.leader(0), n - 1)
        self.assertTrue(all(p == n - 1 for p in tree.par))
        n = 45
        rng = random.Random(0)
        for op in (min, max):
            values = [rng.randrange(7) for _ in range(n)]
            tree = QueryDSU(n, lambda i: values[i], op)
            parents = list(range(n))
            for _ in range(n - 1):
                roots = [i for i in range(n) if parents[i] == i]
                child, root = rng.sample(roots, 2)
                candidates = []
                for i in range(n):
                    v = i
                    while parents[v] != v:
                        v = parents[v]
                    if v == root:
                        candidates.append(i)
                parent = rng.choice(candidates)
                tree.link(child=child, parent=parent)
                parents[child] = parent
                for i in range(n):
                    path = [i]
                    while parents[path[-1]] != path[-1]:
                        path.append(parents[path[-1]])
                    expected = path[0]
                    for v in path[1:]:
                        if op(values[expected], values[v]) == values[v]:
                            expected = v
                    self.assertEqual(tree.eval(i), expected)
                    self.assertEqual(tree.leader(i), path[-1])
            for child, parent in ((-1, 0), (0, n)):
                before = tree.par[:], tree.m[:]
                with self.assertRaises(AssertionError):
                    tree.link(child=child, parent=parent)
                self.assertEqual((tree.par, tree.m), before)

    def test_parallel_merges_and_path_halving(self) -> None:
        n = 35
        rng = random.Random(0)
        weights = [rng.randrange(-10, 11) for _ in range(n)]
        tree = RangeParallelDSU(n, weights, int.__add__, int.__mul__, int.__add__, 0)
        plain = DSUOnlyPathHalving(n)
        labels = list(range(n))
        for _ in range(700):
            length = rng.randrange(n + 1)
            a, b = rng.randrange(n - length + 1), rng.randrange(n - length + 1)
            tree.range_merge(length, a, b)
            for i in range(length):
                if labels[a + i] != labels[b + i]:
                    plain.link(a + i, b + i)
                    labels = merged(labels, a + i, b + i)
            expected = sum(weights[i] * weights[j] for i in range(n) for j in range(i) if labels[i] == labels[j])
            self.assertEqual(tree.pair_sum(), expected)
            x, y = rng.randrange(n), rng.randrange(n)
            self.assertEqual(tree.comp_weight(x), sum(weights[i] for i in range(n) if labels[i] == labels[x]))
            self.assertEqual(tree.same(x, y), labels[x] == labels[y])
            self.assertEqual(plain.same(x, y), labels[x] == labels[y])
            self.assertEqual(labels[plain.leader(x)], labels[x])
        before = [uf.par_size[:] for uf in tree.ufs], tree.vals[:], tree.pair_sum()
        for length, a, b in ((-1, 0, 0), (1, -1, 0), (n + 1, 0, 0), (1, n, 0)):
            with self.assertRaises(AssertionError):
                tree.range_merge(length, a, b)
            self.assertEqual(([uf.par_size for uf in tree.ufs], tree.vals, tree.pair_sum()), before)

    def test_negative_capacity(self) -> None:
        constructors = (DisjointSetUnion, WeightedDSU, PartiallyPersistentDSU, UndoableDSU, DSUOnlyPathHalving, lambda n: DSUWithPotential(n, int.__add__, int.__neg__, 0), lambda n: QueryDSU(n, lambda x: x, min))
        for cls in constructors:
            with self.assertRaises(ValueError):
                cls(-1)


if __name__ == '__main__':
    unittest.main()
