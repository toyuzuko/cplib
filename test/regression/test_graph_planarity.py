import copy
import itertools
import random
import sys
import unittest

from cplib.graph import PlanarEmbeddingResult, is_planar, planar_dual, planar_embedding, planar_faces
from cplib.graph.base import Node, Weight
from cplib.graph.core import Graph
from cplib.graph.families import is_planar as families_is_planar
from cplib.graph.lowlink import lowlink


def _graph(n: int, edges: list[tuple[int, int]]) -> Graph:
    graph = Graph(n)
    for u, v in edges:
        graph.add_edge(Node(u), Node(v))
    return graph


def _small_planarity(n: int, edges: list[tuple[int, int]]) -> bool:
    """Independent forbidden-minor oracle for simple graphs on at most six vertices.

    A K3,3 minor must use six singleton branch sets. A K5 minor either uses
    five singletons, or contracts one edge of a six-vertex subgraph.
    """
    assert n <= 6
    if len(edges) < 9:
        return True
    adjacent = [0] * n
    for u, v in edges:
        adjacent[u] |= 1 << v
        adjacent[v] |= 1 << u
    for vertices in itertools.combinations(range(n), 5):
        if all(adjacent[u] >> v & 1 for u, v in itertools.combinations(vertices, 2)):
            return False
    if n == 6:
        for other in itertools.combinations(range(1, n), 2):
            left = (0, *other)
            right = ((1 << n) - 1) ^ sum(1 << v for v in left)
            if all(adjacent[v] & right == right for v in left):
                return False
        for u, v in edges:
            remaining = [w for w in range(n) if w != u and w != v]
            if all((adjacent[u] | adjacent[v]) >> w & 1 for w in remaining) and all(
                adjacent[a] >> b & 1 for a, b in itertools.combinations(remaining, 2)
            ):
                return False
    return True


def _subdivide(n: int, edges: list[tuple[int, int]], count: int) -> tuple[int, list[tuple[int, int]]]:
    result: list[tuple[int, int]] = []
    for u, v in edges:
        for _ in range(count):
            result.append((u, n))
            u = n
            n += 1
        result.append((u, v))
    return n, result


class PlanarityTest(unittest.TestCase):
    def test_empty_loops_parallel_edges_and_weights(self) -> None:
        for n in range(8):
            self.assertTrue(is_planar(Graph(n)))
        graph = Graph(7, connectivity_check=True)
        for u in range(7):
            graph.add_edge(Node(u), Node(u), Weight(-10))
            for _ in range(20):
                graph.add_edge(Node(u), Node((u + 1) % 7), Weight(0))
                graph.add_edge(Node((u + 1) % 7), Node(u), Weight(100))
        before = copy.deepcopy(vars(graph))
        before['dsu'] = graph.dsu
        before_dsu = copy.deepcopy(vars(graph.dsu))
        for _ in range(2):
            self.assertTrue(is_planar(graph))
            self.assertEqual(vars(graph), before)
            self.assertEqual(vars(graph.dsu), before_dsu)

        graph = _graph(6, [(u, v) for u in range(3) for v in range(3, 6)])
        for u, v in graph.edges[:]:
            graph.add_edge(v, u, Weight(-1))
            graph.add_edge(u, u)
        before = copy.deepcopy(vars(graph))
        for _ in range(2):
            self.assertFalse(is_planar(graph))
            self.assertEqual(vars(graph), before)

    def test_directed_graphs_are_rejected(self) -> None:
        for n in (0, 1, 6):
            with self.assertRaises(ValueError):
                is_planar(Graph(n, is_directed=True))

    def test_all_six_vertex_graphs_against_forbidden_minors(self) -> None:
        possible = list(itertools.combinations(range(6), 2))
        for mask in range(1 << len(possible)):
            edges = [edge for i, edge in enumerate(possible) if mask >> i & 1]
            self.assertEqual(is_planar(_graph(6, edges)), _small_planarity(6, edges), f'{mask=}, {edges=}')

    def test_subdivisions_and_traversal_orders(self) -> None:
        k4 = list(itertools.combinations(range(4), 2))
        k5 = list(itertools.combinations(range(5), 2))
        k33 = [(u, v) for u in range(3) for v in range(3, 6)]
        cube = [(u, u ^ (1 << bit)) for u in range(8) for bit in range(3) if u < u ^ (1 << bit)]
        octahedron = [(u, v) for u, v in itertools.combinations(range(6), 2) if u // 2 != v // 2]
        petersen = [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + [(i + 5, (i + 2) % 5 + 5) for i in range(5)]
        rng = random.Random(7)
        for n, edges, expected in ((4, k4, True), (5, k5, False), (6, k33, False), (8, cube, True), (6, octahedron, True), (10, petersen, False)):
            for subdivisions in (0, 1, 3):
                size, divided = _subdivide(n, edges, subdivisions)
                for _ in range(12):
                    labels = list(range(size))
                    rng.shuffle(labels)
                    shuffled = [(labels[v], labels[u]) if rng.randrange(2) else (labels[u], labels[v]) for u, v in divided]
                    rng.shuffle(shuffled)
                    with self.subTest(n=n, subdivisions=subdivisions, expected=expected):
                        self.assertEqual(is_planar(_graph(size, shuffled)), expected)

    def test_disconnected_graphs_and_articulations(self) -> None:
        edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]
        self.assertTrue(is_planar(_graph(20, edges)))
        edges += [(u, v) for u in range(6, 9) for v in range(9, 12)]
        self.assertFalse(is_planar(_graph(30, edges)))
        edges = []
        # K4 blocks joined at articulation vertices, with many DFS roots.
        for first in range(0, 60, 3):
            edges.extend(itertools.combinations(range(first, first + 4), 2))
        self.assertTrue(is_planar(_graph(100, edges)))
        edges += [(u, v) for u in range(60, 63) for v in range(63, 66)]
        self.assertFalse(is_planar(_graph(100, edges)))

    def test_large_sparse_families_without_recursion(self) -> None:
        limit = sys.getrecursionlimit()
        n = 6000
        path = [(v, v + 1) for v in range(n - 1)]
        self.assertTrue(is_planar(_graph(n, path)))
        self.assertTrue(is_planar(_graph(n, path + [(n - 1, 0)])))
        wheel = [(0, v) for v in range(1, n)] + [(v, v + 1) for v in range(1, n - 1)] + [(n - 1, 1)]
        self.assertTrue(is_planar(_graph(n, wheel)))
        self.assertTrue(is_planar(_graph(n, [(u, v) for u in range(2) for v in range(2, n)])))
        self.assertFalse(is_planar(_graph(n, [(u, v) for u in range(3) for v in range(3, n)])))
        width = 35
        grid = [(r * width + c, (r + 1) * width + c) for r in range(width - 1) for c in range(width)]
        grid += [(r * width + c, r * width + c + 1) for r in range(width) for c in range(width - 1)]
        self.assertTrue(is_planar(_graph(width * width, grid)))
        self.assertEqual(sys.getrecursionlimit(), limit)


class PlanarEmbeddingTest(unittest.TestCase):
    def assert_embedding(self, graph: Graph, expected: bool = True) -> PlanarEmbeddingResult | None:
        embedding = planar_embedding(graph)
        self.assertEqual(embedding is not None, expected)
        if embedding is None:
            return None
        self.assertEqual(embedding.edges, graph.edges)
        self.assertEqual(embedding.weights, graph.wt)
        self.assertEqual(len(embedding.rotation), graph.n)
        self.assertEqual(sorted(h for row in embedding.rotation for h in row), list(range(2 * graph.m)))
        for v, row in enumerate(embedding.rotation):
            for h in row:
                self.assertEqual(graph.edges[h // 2][h & 1], v)

        # Verify the certificate using Euler's formula, independently of LR.
        components: list[set[int]] = []
        seen: set[int] = set()
        for root in range(graph.n):
            if root in seen:
                continue
            members = {root}
            seen.add(root)
            pending = [root]
            while pending:
                v = pending.pop()
                for w, _ in graph.graph[v]:
                    if w not in seen:
                        seen.add(w)
                        members.add(w)
                        pending.append(w)
            components.append(members)
        self.assertEqual(len(embedding.component), graph.n)
        self.assertEqual(set(embedding.component), set(range(len(components))))
        for members in components:
            self.assertEqual(len({embedding.component[v] for v in members}), 1)

        faces = planar_faces(embedding)
        self.assertEqual(graph.n - graph.m + len(faces.boundaries), 1 + len(components))
        self.assertEqual(sorted(h for walks in faces.boundaries for walk in walks for h in walk), list(range(2 * graph.m)))
        self.assertEqual(len(faces.face_of_half_edge), 2 * graph.m)
        edge_components = sum(any(graph.graph[v] for v in members) for members in components)
        self.assertEqual(len(faces.boundaries[0]), edge_components)
        for face, walks in enumerate(faces.boundaries):
            if face:
                self.assertEqual(len(walks), 1)
            for walk in walks:
                self.assertTrue(walk)
                for h, following in zip(walk, walk[1:] + walk[:1]):
                    self.assertEqual(faces.face_of_half_edge[h], face)
                    target = graph.edges[h // 2][(h & 1) ^ 1]
                    self.assertEqual(target, graph.edges[following // 2][following & 1])
                    row = embedding.rotation[target]
                    self.assertEqual(row[(row.index(h ^ 1) + 1) % len(row)], following)

        dual = planar_dual(embedding)
        self.assertEqual(dual.n, len(faces.boundaries))
        self.assertEqual(dual.m, graph.m)
        self.assertEqual(dual.wt, graph.wt)
        self.assertEqual(dual.edges, [(faces.face_of_half_edge[2 * e], faces.face_of_half_edge[2 * e + 1]) for e in range(graph.m)])
        self.assertEqual({e for e, (u, v) in enumerate(dual.edges) if u == v}, set(lowlink(graph).bridges))
        self.assertTrue(is_planar(dual))
        return embedding

    def test_all_six_vertex_graphs_have_valid_certificates(self) -> None:
        possible = list(itertools.combinations(range(6), 2))
        for mask in range(1 << len(possible)):
            edges = [edge for i, edge in enumerate(possible) if mask >> i & 1]
            with self.subTest(mask=mask):
                self.assert_embedding(_graph(6, edges), _small_planarity(6, edges))

    def test_empty_isolated_loops_parallel_edges_and_weights(self) -> None:
        for n in range(8):
            self.assert_embedding(Graph(n))
            self.assert_embedding(_graph(n, [(v, v) for v in range(n)]))
        graph = Graph(6)
        for u, v in ((0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)):
            for i in range(4):
                a, b = (u, v) if i % 2 else (v, u)
                graph.add_edge(Node(a), Node(b), Weight(i - 2))
        for v in range(6):
            graph.add_edge(Node(v), Node(v), Weight(100))
            graph.add_edge(Node(v), Node(v), Weight(-100))
        before = copy.deepcopy(vars(graph))
        self.assert_embedding(graph)
        self.assertEqual(vars(graph), before)

    def test_disconnected_exteriors_are_one_face(self) -> None:
        edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (6, 6), (6, 6), (7, 8)]
        embedding = self.assert_embedding(_graph(10, edges))
        assert embedding is not None
        faces = planar_faces(embedding)
        self.assertEqual(len(faces.boundaries), 5)
        self.assertEqual(len(faces.boundaries[0]), 4)
        self.assertEqual(sorted(len(walks[0]) for walks in faces.boundaries[1:]), [1, 1, 3, 3])

    def test_snapshot_and_legacy_import(self) -> None:
        self.assertIs(families_is_planar, is_planar)
        graph = _graph(4, list(itertools.combinations(range(4), 2)))
        embedding = self.assert_embedding(graph)
        assert embedding is not None
        saved = copy.deepcopy(embedding)
        original_faces = planar_faces(embedding)
        graph.add_edge(Node(0), Node(0), Weight(99))
        graph.wt[0] = Weight(-8)
        graph.edges[0] = graph.edges[1]
        self.assertEqual(embedding, saved)
        self.assertEqual(planar_faces(embedding), original_faces)
        dual = planar_dual(embedding)
        self.assertEqual((dual.n, dual.m), (4, 6))
        self.assertEqual(len({frozenset(edge) for edge in dual.edges}), 6)

    def test_random_multigraphs_and_stacked_triangulations(self) -> None:
        rng = random.Random(51)
        for _ in range(120):
            possible = list(itertools.combinations(range(6), 2))
            simple = rng.sample(possible, rng.randrange(len(possible) + 1))
            edges = [(v, u) if rng.randrange(2) else (u, v) for u, v in simple for _ in range(rng.randrange(1, 5))]
            edges += [(v, v) for v in range(6) for _ in range(rng.randrange(3))]
            rng.shuffle(edges)
            self.assert_embedding(_graph(6, edges), _small_planarity(6, simple))
        for n in (8, 30, 100):
            for _ in range(12):
                edges = [(0, 1), (1, 2), (2, 0)]
                faces = [(0, 1, 2)]
                for v in range(3, n):
                    index = rng.randrange(len(faces))
                    a, b, c = faces[index]
                    faces[index] = faces[-1]
                    faces.pop()
                    edges.extend(((v, a), (v, b), (v, c)))
                    faces.extend(((a, b, v), (b, c, v), (c, a, v)))
                labels = list(range(n))
                rng.shuffle(labels)
                edges = [(labels[u], labels[v]) for u, v in edges]
                rng.shuffle(edges)
                self.assert_embedding(_graph(n, edges))

    def test_deep_embeddings_and_directed_rejection(self) -> None:
        for n in (0, 1, 6):
            with self.assertRaises(ValueError):
                planar_embedding(Graph(n, is_directed=True))
        n = 6000
        path = [(v, v + 1) for v in range(n - 1)]
        self.assert_embedding(_graph(n, path))
        self.assert_embedding(_graph(n, path + [(0, n - 1)]))
        # A deep DFS with repeated nested triangles and no recursion.
        self.assert_embedding(_graph(n, path + [(v, v + 2) for v in range(n - 2)]))


if __name__ == '__main__':
    unittest.main()
