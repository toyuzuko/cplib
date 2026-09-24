import random
import unittest
from operator import add

from cplib.graph.toptree import TopTree


def forest_root(parents: list[int], vertex: int) -> int:
    while parents[vertex] != -1:
        vertex = parents[vertex]
    return vertex


def reroot(parents: list[int], vertex: int) -> None:
    previous = -1
    while vertex != -1:
        parent = parents[vertex]
        parents[vertex] = previous
        previous, vertex = vertex, parent


def descendants(parents: list[int], vertex: int) -> list[int]:
    result = [vertex]
    for current in result:
        result.extend(v for v, p in enumerate(parents) if p == current)
    return result


def diameter_rake(left: tuple[int, int, int], right: tuple[int, int, int]) -> tuple[int, int, int]:
    heights = sorted((left[0], left[1], right[0], right[1]), reverse=True)
    return heights[0], heights[1], max(left[2], right[2])


def diameter_vertex(point: tuple[int, int, int], value: int) -> tuple[int, int, int, int]:
    return value, value + point[0], value + point[0], max(point[2], value + point[0] + point[1])


def diameter_edge(path: tuple[int, int, int, int]) -> tuple[int, int, int]:
    return path[1], 0, path[3]


def diameter_compress(upper: tuple[int, int, int, int], lower: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return (upper[0] + lower[0], max(upper[1], upper[0] + lower[1]),
            max(lower[2], lower[0] + upper[2]), max(upper[3], lower[3], upper[2] + lower[1]))


def weighted_distances(parents: list[int], values: list[int], start: int, allowed: set[int]) -> dict[int, int]:
    adjacency: list[list[int]] = [[] for _ in parents]
    for child, parent in enumerate(parents):
        if parent != -1:
            adjacency[child].append(parent)
            adjacency[parent].append(child)
    distances = {start: values[start]}
    stack = [start]
    while stack:
        vertex = stack.pop()
        for to in adjacency[vertex]:
            if to in allowed and to not in distances:
                distances[to] = distances[vertex] + values[to]
                stack.append(to)
    return distances


class TopTreeTest(unittest.TestCase):
    def test_random_forest_without_inverse(self) -> None:
        for seed in range(5):
            rng = random.Random(seed)
            n = 14
            values = [rng.randrange(30) for _ in range(n)]
            parents = [-1] * n
            maximum = TopTree(values, 0, max, lambda path: path, max, max)
            diameter = TopTree(values, (0, 0, 0), diameter_vertex, diameter_edge, diameter_rake, diameter_compress)
            for step in range(500):
                u, v = rng.sample(range(n), 2)
                operation = rng.randrange(9)
                with self.subTest(seed=seed, step=step, operation=operation):
                    trees = (maximum, diameter)
                    if operation == 0:
                        if forest_root(parents, u) == forest_root(parents, v):
                            for tree in trees:
                                with self.assertRaises(ValueError):
                                    tree.link(child=u, parent=v)
                        else:
                            for tree in trees:
                                tree.link(child=u, parent=v)
                            reroot(parents, u)
                            parents[u] = v
                    elif operation == 1:
                        edges = [(child, p) for child, p in enumerate(parents) if p != -1]
                        if edges:
                            child, parent = rng.choice(edges)
                            u, v = (child, parent) if rng.randrange(2) else (parent, child)
                            for tree in trees:
                                tree.cut(u, v)
                            parents[child] = -1
                            reroot(parents, parent)
                    elif operation == 2:
                        for tree in trees:
                            if parents[u] == -1:
                                with self.assertRaises(ValueError):
                                    tree.cut_parent(u)
                            else:
                                tree.cut_parent(u)
                        parents[u] = -1
                    elif operation == 3:
                        for tree in trees:
                            tree.reroot(u)
                        reroot(parents, u)
                    elif operation == 4:
                        values[u] = rng.randrange(30)
                        for tree in trees:
                            tree.set(u, values[u])
                    elif operation == 5:
                        if parents[u] != v and parents[v] != u:
                            for tree in trees:
                                with self.assertRaises(ValueError):
                                    tree.cut(u, v)
                    elif operation == 6:
                        maximum.access(u)
                        diameter.access(u)
                    elif operation == 7:
                        component = set(descendants(parents, forest_root(parents, u)))
                        self.assertEqual(maximum.tree_value(u), max(values[x] for x in component))
                        result = diameter.tree_value(u)
                        distances = weighted_distances(parents, values, u, component)
                        expected_diameter = max(max(weighted_distances(parents, values, x, component).values()) for x in component)
                        self.assertEqual((result[1], result[3]), (max(distances.values()), expected_diameter))
                        reroot(parents, u)
                    else:
                        if forest_root(parents, u) == forest_root(parents, v):
                            component = set(descendants(parents, forest_root(parents, u)))
                            distances = weighted_distances(parents, values, u, component)
                            result = diameter.path_cluster_value(u, v)
                            self.assertEqual(result[0], distances[v])
                            self.assertEqual(result[1], max(distances.values()))
                            self.assertEqual(result[2], max(weighted_distances(parents, values, v, component).values()))
                            self.assertEqual(maximum.path_cluster_value(u, v), max(values[x] for x in component))
                            reroot(parents, u)
                        else:
                            for tree in trees:
                                with self.assertRaises(ValueError):
                                    tree.path_cluster_value(u, v)
                                with self.assertRaises(ValueError):
                                    tree.subtree_value(u, root=v)
                    for tree in trees:
                        for x in range(n):
                            self.assertEqual(tree.root(x), forest_root(parents, x))
                            self.assertEqual(tree.parent(x), parents[x])
                            self.assertEqual(tree.get(x), values[x])
                        self.assertEqual(tree.same(u, v), forest_root(parents, u) == forest_root(parents, v))
                    vertices = set(descendants(parents, u))
                    self.assertEqual(maximum.subtree_value(u), max(values[x] for x in vertices))
                    result = diameter.subtree_value(u)
                    self.assertEqual(result[1], max(weighted_distances(parents, values, u, vertices).values()))
                    self.assertLessEqual(len(maximum._r_parent), n - 1)
                    self.assertLessEqual(len(diameter._r_parent), n - 1)

    def test_noncommutative_path_composition(self) -> None:
        mod = 998244353
        def compose(upper: tuple[int, int], lower: tuple[int, int]) -> tuple[int, int]:
            return upper[0] * lower[0] % mod, (upper[0] * lower[1] + upper[1]) % mod
        rng = random.Random(3)
        n = 35
        values = [(rng.randrange(10), rng.randrange(10)) for _ in range(n)]
        tree = TopTree(values, None, lambda point, value: value, lambda path: None, lambda a, b: None, compose)
        parents = [-1] * n
        for v in range(1, n):
            parents[v] = rng.randrange(v)
            tree.link(v, parents[v])
        for _ in range(600):
            u, v = rng.sample(range(n), 2)
            if rng.randrange(3) == 0:
                values[u] = rng.randrange(10), rng.randrange(10)
                tree.set(u, values[u])
            result = tree.path_cluster_value(u, v)
            reroot(parents, u)
            path = [v]
            while parents[path[-1]] != -1:
                path.append(parents[path[-1]])
            expected = (1, 0)
            for x in reversed(path):
                expected = compose(expected, values[x])
            self.assertEqual(result, expected)
            if rng.randrange(5) == 0:
                child = rng.choice([x for x, p in enumerate(parents) if p != -1])
                parent = parents[child]
                tree.cut(child, parent)
                parents[child] = -1
                reroot(parents, parent)
                component = descendants(parents, child)
                child = rng.choice(component)
                parent = rng.choice([x for x in range(n) if x not in component])
                tree.link(child, parent)
                reroot(parents, child)
                parents[child] = parent

    def test_diameter_after_sparse_queries_and_edge_replacements(self) -> None:
        rng = random.Random(71)
        n = 45
        values = [rng.randrange(20) for _ in range(n)]
        parents = [-1] + [rng.randrange(v) for v in range(1, n)]
        tree = TopTree(values, (0, 0, 0), diameter_vertex, diameter_edge, diameter_rake, diameter_compress)
        for child in range(1, n):
            tree.link(child, parents[child])
        for step in range(350):
            vertex = rng.randrange(n)
            values[vertex] = rng.randrange(20)
            tree.set(vertex, values[vertex])
            child = rng.choice([v for v, p in enumerate(parents) if p != -1])
            parent = parents[child]
            tree.cut(child, parent)
            parents[child] = -1
            reroot(parents, parent)
            component = descendants(parents, child)
            child = rng.choice(component)
            parent = rng.choice([v for v in range(n) if v not in component])
            tree.link(child, parent)
            reroot(parents, child)
            parents[child] = parent
            if step % 7 == 0:
                root = rng.randrange(n)
                vertex = rng.randrange(n)
                result = tree.subtree_value(vertex, root=root)
                reroot(parents, root)
                vertices = set(descendants(parents, vertex))
                expected = max(max(weighted_distances(parents, values, v, vertices).values()) for v in vertices)
                self.assertEqual(result[3], expected)
                self.assertEqual(result[1], max(weighted_distances(parents, values, vertex, vertices).values()))
            if step % 11 == 0:
                root = rng.randrange(n)
                result = tree.tree_value(root)
                vertices = set(range(n))
                expected = max(max(weighted_distances(parents, values, v, vertices).values()) for v in vertices)
                self.assertEqual(result[3], expected)
                reroot(parents, root)

    def test_boundaries_and_empty_forest(self) -> None:
        for n in (0, 1, 4):
            tree = TopTree(list(range(n)), 0, add, lambda path: path, add, add)
            for vertex in (-1, n):
                for operation in (tree.get, tree.root, tree.parent, tree.reroot, tree.access, tree.tree_value, tree.subtree_value, tree.cut_parent):
                    with self.assertRaises(IndexError):
                        operation(vertex)
                with self.assertRaises(IndexError):
                    tree.set(vertex, 1)
                for operation in (tree.same, tree.link, tree.cut, tree.path_cluster_value):
                    with self.assertRaises(IndexError):
                        operation(vertex, vertex)
                    if n:
                        with self.assertRaises(IndexError):
                            operation(0, vertex)
                        with self.assertRaises(IndexError):
                            operation(vertex, 0)
                if n:
                    with self.assertRaises(IndexError):
                        tree.subtree_value(0, root=vertex)
            if n:
                self.assertTrue(tree.same(0, 0))
                self.assertEqual(tree.root(0), 0)
                self.assertEqual(tree.parent(0), -1)
                with self.assertRaises(ValueError):
                    tree.link(0, 0)
                with self.assertRaises(ValueError):
                    tree.cut(0, 0)
                with self.assertRaises(ValueError):
                    tree.cut_parent(0)

    def test_reuse_on_star_and_repeated_updates(self) -> None:
        n = 120
        values = list(range(n))
        tree = TopTree(values, 0, max, lambda path: path, max, max)
        for child in range(1, n):
            tree.link(child, 0)
        for step in range(1200):
            child = 1 + step % (n - 1)
            tree.cut(child, 0)
            self.assertEqual(tree.tree_value(child), values[child])
            tree.set(child, step + n)
            values[child] = step + n
            tree.link(child, 0)
            self.assertEqual(tree.tree_value(0), max(values))
            self.assertLessEqual(len(tree._r_parent), n - 1)
        for child in range(1, n):
            tree.cut(child, 0)
        self.assertEqual(len(tree._free), len(tree._r_parent))
        self.assertTrue(all(value == 0 for value in tree._r_key))


if __name__ == '__main__':
    unittest.main()
