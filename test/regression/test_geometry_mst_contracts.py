from fractions import Fraction
from itertools import combinations, product
from random import Random
import unittest

from cplib.geometry.integer import Point, delaunay_edges, euclidean_mst, manhattan_mst


Coord = tuple[int, int]


def metric(a: Coord, b: Coord, euclidean: bool) -> int:
    dx, dy = a[0]-b[0], a[1]-b[1]
    return dx*dx+dy*dy if euclidean else abs(dx)+abs(dy)


def prim_weights(points: list[Coord], euclidean: bool) -> list[int]:
    n = len(points)
    if not n:
        return []
    used = [False]*n
    distances: list[int | None] = [None]*n
    distances[0] = 0
    weights: list[int] = []
    for step in range(n):
        _, u = min((d, i) for i, d in enumerate(distances) if not used[i] and d is not None)
        used[u] = True
        if step:
            weights.append(distances[u])
        for v in range(n):
            if not used[v]:
                w = metric(points[u], points[v], euclidean)
                if distances[v] is None or w < distances[v]:
                    distances[v] = w
    return sorted(weights)


def orientation(a: Coord, b: Coord, c: Coord) -> int:
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def has_empty_circle(points: list[Coord], a: Coord, b: Coord) -> bool:
    # Centers through a,b lie on their perpendicular bisector. Every other
    # point imposes a linear bound on its parameter; solve those inequalities.
    mx, my = Fraction(a[0]+b[0], 2), Fraction(a[1]+b[1], 2)
    nx, ny = a[1]-b[1], b[0]-a[0]
    radius2 = (a[0]-mx)**2+(a[1]-my)**2
    lower: Fraction | None = None
    upper: Fraction | None = None
    for x, y in points:
        coefficient = 2*(nx*(x-mx)+ny*(y-my))
        bound = (x-mx)**2+(y-my)**2-radius2
        if coefficient == 0:
            if bound < 0:
                return False
        elif coefficient > 0:
            value = bound/coefficient
            upper = value if upper is None else min(upper, value)
        else:
            value = bound/coefficient
            lower = value if lower is None else max(lower, value)
    return lower is None or upper is None or lower <= upper


class GeometryMSTContractsTest(unittest.TestCase):
    def assert_tree(self, n: int, edges: list[tuple[int, int]]) -> None:
        self.assertEqual(len(edges), max(n-1, 0))
        adjacent: list[list[int]] = [[] for _ in range(n)]
        for u, v in edges:
            self.assertTrue(0 <= u < n and 0 <= v < n and u != v)
            adjacent[u].append(v)
            adjacent[v].append(u)
        seen = {0} if n else set()
        stack = list(seen)
        while stack:
            for v in adjacent[stack.pop()]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        self.assertEqual(len(seen), n)

    def test_msts_against_complete_graph(self) -> None:
        rng = Random(0)
        cases: list[list[Coord]] = [[], [(0, 0)], [(2, 3)]*20]
        circle = [(x, y) for x, y in product(range(-5, 6), repeat=2) if x*x+y*y == 25]
        for size in range(2, len(circle)+1):
            cases.append(circle[:size])
        cases += [[(1, -5), (-1, 3), (2, 1), (-1, 2), (0, 4), (-2, 3), (-3, -1), (-3, -4)]]
        for _ in range(500):
            points = [(rng.randrange(-15, 16), rng.randrange(-15, 16)) for _ in range(rng.randrange(22))]
            if rng.randrange(4) == 0:
                points = [(x, 3*x-2) for x, _ in points]
            cases.append(points)
        for raw in cases:
            expected_manhattan = prim_weights(raw, False)
            expected_euclidean = prim_weights(raw, True)
            # Preserve distances but move far beyond any machine-integer sentinel.
            for dx, dy in ((0, 0), (10**40, -(10**45)), (-10**50, 10**60)):
                points = [Point(x+dx, y+dy) for x, y in raw]
                before = [(p.x, p.y) for p in points]
                edges, total = manhattan_mst(points)
                self.assert_tree(len(raw), edges)
                self.assertEqual(total, sum(expected_manhattan))
                self.assertEqual(sorted(metric(raw[u], raw[v], False) for u, v in edges), expected_manhattan)
                edges = euclidean_mst(points)
                self.assert_tree(len(raw), edges)
                self.assertEqual(edges, sorted(edges))
                self.assertTrue(all(u < v for u, v in edges))
                self.assertEqual(sorted(metric(raw[u], raw[v], True) for u, v in edges), expected_euclidean)
                self.assertEqual([(p.x, p.y) for p in points], before)

    def test_delaunay_geometry_and_degeneracies(self) -> None:
        rng = Random(0)
        cases: list[list[Coord]] = [[], [(0, 0)], [(1, 2)]*9]
        cases += [list(points) for size in range(2, 6) for points in combinations(list(product(range(2), range(3))), size)]
        cases += [[(x, 2*x+1) for x in range(-5, 6)], [(x, 0) for x in range(-5, 6)], [(0, y) for y in range(-5, 6)]]
        cases += [[(x, y) for x, y in product(range(-5, 6), repeat=2) if x*x+y*y == 25]]
        for _ in range(200):
            cases.append([(rng.randrange(-5, 6), rng.randrange(-5, 6)) for _ in range(rng.randrange(2, 15))])
        for raw in cases:
            points = [Point(x, y) for x, y in raw]
            edges = delaunay_edges(points)
            self.assertEqual(len({tuple(sorted(edge)) for edge in edges}), len(edges))
            unique = list(dict.fromkeys(raw))
            geometric: list[tuple[Coord, Coord]] = []
            duplicates: set[tuple[int, int]] = set()
            for u, v in edges:
                self.assertTrue(0 <= u < len(raw) and 0 <= v < len(raw) and u != v)
                a, b = raw[u], raw[v]
                if a == b:
                    duplicates.add(tuple(sorted((u, v))))
                else:
                    self.assertEqual((u, v), (raw.index(a), raw.index(b)))
                    self.assertTrue(has_empty_circle(unique, a, b), (raw, a, b))
                    geometric.append((a, b))
            self.assertEqual(duplicates, {tuple(sorted((i, raw.index(p)))) for i, p in enumerate(raw) if i != raw.index(p)})
            for (a, b), (c, d) in combinations(geometric, 2):
                if a not in (c, d) and b not in (c, d):
                    self.assertFalse(orientation(a, b, c)*orientation(a, b, d) < 0 and orientation(c, d, a)*orientation(c, d, b) < 0)
            if len(unique) >= 2 and all(orientation(unique[0], unique[1], p) == 0 for p in unique):
                ordered = sorted(unique)
                self.assertEqual({tuple(sorted(edge)) for edge in geometric}, set(zip(ordered, ordered[1:])))
            elif len(unique) >= 3:
                boundary = set()
                for a, b in combinations(unique, 2):
                    turns = [orientation(a, b, p) for p in unique]
                    if min(turns) >= 0 or max(turns) <= 0:
                        boundary.update((a, b))
                self.assertEqual(len(geometric), 3*len(unique)-3-len(boundary))
            self.assertEqual([(p.x, p.y) for p in points], raw)


if __name__ == '__main__':
    unittest.main()
