from fractions import Fraction
from itertools import combinations
from math import hypot, sqrt
from random import Random
import unittest

from cplib.geometry import floating as g
from test.regression.test_geometry_exact_contracts import Coord, cross, hull, on_segment


def area(points: list[Coord]) -> Fraction:
    return sum((a[0]*b[1]-a[1]*b[0] for a, b in zip(points, points[1:]+points[:1])), Fraction(0))/2


def winding(points: list[Coord], p: Coord) -> int:
    count = 0
    for a, b in zip(points, points[1:]+points[:1]):
        if on_segment(a, b, p):
            return 1
        if a[1] <= p[1] < b[1] and cross(a, b, p) > 0:
            count += 1
        elif b[1] <= p[1] < a[1] and cross(a, b, p) < 0:
            count -= 1
    return 2 if count else 0


def points(raw: list[Coord]) -> list[g.Point]:
    return [g.Point(float(x), float(y)) for x, y in raw]


class FloatingPolygonContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.eps = g.get_eps()
        g.set_eps(1e-10)

    def tearDown(self) -> None:
        g.set_eps(self.eps)

    def test_areas_convexity_and_membership(self) -> None:
        rng = Random(0)
        cases: list[list[Coord]] = [[], [(Fraction(0), Fraction(0))], [(Fraction(0), Fraction(0)), (Fraction(2), Fraction(2))], [(Fraction(x), Fraction(0)) for x in range(4)]]
        for _ in range(120):
            raw = [(Fraction(rng.randrange(-10, 11)), Fraction(rng.randrange(-10, 11))) for _ in range(12)]
            cases.append([raw[i] for i in hull(raw)])
            w, h = rng.randrange(3, 12), rng.randrange(3, 12)
            a, b = rng.randrange(1, w), rng.randrange(1, h)
            cases.append([(Fraction(x), Fraction(y)) for x, y in [(0, 0), (w, 0), (w, h), (a, h), (a, b), (0, b)]])
        for raw in cases:
            for dx, dy in ((0, 0), (10**9, -10**9)):
                translated = [(x+dx, y+dy) for x, y in raw]
                for order in (translated, translated[::-1]):
                    polygon = points(order)
                    expected = area(order)
                    self.assertEqual(g.polygon_signed_area(polygon), float(expected))
                    self.assertEqual(g.polygon_area(polygon), float(abs(expected)))
                    self.assertEqual(g.polygon_area(polygon+polygon[:1]), float(abs(expected)))
            if len(raw) >= 3 and area(raw):
                # A convex simple polygon lies in one closed half-plane of
                # each of its supporting edge lines.
                turns = [cross(a, b, p) for a, b in zip(raw, raw[1:]+raw[:1]) for p in raw]
                convex = min(turns) >= 0 or max(turns) <= 0
            else:
                convex = False
            self.assertEqual(g.is_convex_polygon(points(raw)), convex)
            self.assertEqual(g.is_convex_polygon(points(raw[::-1])), convex)
            strict = convex and all(cross(raw[i-1], raw[i], raw[(i+1) % len(raw)]) != 0 for i in range(len(raw)))
            self.assertEqual(g.is_convex_polygon(points(raw), allow_collinear=False), strict)
            for _ in range(25):
                p = Fraction(rng.randrange(-12, 13)), Fraction(rng.randrange(-12, 13))
                expected = winding(raw, p)
                for polygon in (raw, raw[::-1], [a for a in raw for _ in range(2)]+raw[:1]):
                    self.assertEqual(g.contains_point_in_polygon(points(polygon), g.Point(float(p[0]), float(p[1]))), expected)
        for n in range(1, 5):
            repeated = [g.Point(0, 0)]*n
            self.assertEqual(g.contains_point_in_polygon(repeated, g.Point(1e-11, 0)), g.POINT_ON_POLYGON)
            self.assertEqual(g.contains_point_in_polygon(repeated, g.Point(1e-6, 0)), g.POINT_OUTSIDE_POLYGON)

    def test_hulls_and_diameters(self) -> None:
        rng = Random(0)
        for _ in range(400):
            raw = [(Fraction(rng.randrange(-8, 9)), Fraction(rng.randrange(-8, 9))) for _ in range(rng.randrange(25))]
            if rng.randrange(4) == 0:
                raw = [(x, 2*x+1) for x, _ in raw]
            extremes = [raw[i] for i in hull(raw)]
            unique = sorted(set(raw))
            if len(extremes) <= 2:
                boundary = unique
            else:
                boundary: list[Coord] = []
                for a, b in zip(extremes, extremes[1:]+extremes[:1]):
                    boundary += sorted((p for p in unique if p != b and on_segment(a, b, p)), key=lambda p: (p[0]-a[0])*(b[0]-a[0])+(p[1]-a[1])*(b[1]-a[1]))
            original = points(raw)
            before = original[:]
            for keep, expected in ((False, extremes), (True, boundary)):
                answer = g.convex_hull(original, keep_collinear=keep)
                self.assertEqual([(p.x, p.y) for p in answer], expected)
                self.assertTrue(all(any(p is source for source in original) for p in answer))
            self.assertEqual([id(p) for p in original], [id(p) for p in before])
            if not boundary:
                with self.assertRaises(ValueError):
                    g.convex_polygon_diameter([])
                continue
            for scale in (1.0, 1e-6):
                polygon = [g.Point(float(x)*scale, float(y)*scale) for x, y in boundary]
                pivot = rng.randrange(len(polygon))
                for order in (polygon, polygon[::-1], polygon[pivot:]+polygon[:pivot], [p for p in polygon for _ in range(2)]+polygon[:1]):
                    i, j, value = g.convex_polygon_diameter(order)
                    expected = max((a.x-b.x)**2+(a.y-b.y)**2 for a in order for b in order)
                    self.assertAlmostEqual(value/(scale*scale), expected/(scale*scale))
                    self.assertEqual(value, (order[i].x-order[j].x)**2+(order[i].y-order[j].y)**2)
        small = [g.Point(0, 0), g.Point(10e-6, 1e-6), g.Point(-10e-6, 1e-6)]
        self.assertAlmostEqual(g.convex_polygon_diameter(small)[2]/1e-12, 400.0)
        # Rounding changes the signs of tiny cross products. Waiting for the
        # two calipers to return simultaneously can loop forever here.
        line = [g.Point(x*1e-6, (2*x+1)*1e-6) for x in (-8, -6, -4, -2, -1, 0, 4, 6, 7)]
        for order in (line, line[::-1]):
            i, j, value = g.convex_polygon_diameter(order)
            expected = max((a.x-b.x)**2+(a.y-b.y)**2 for a in order for b in order)
            self.assertAlmostEqual(value/1e-12, expected/1e-12)
            self.assertEqual(value, (order[i].x-order[j].x)**2+(order[i].y-order[j].y)**2)

    def test_convex_cut(self) -> None:
        rng = Random(0)
        for _ in range(500):
            raw = [(Fraction(rng.randrange(-10, 11)), Fraction(rng.randrange(-10, 11))) for _ in range(12)]
            polygon = [raw[i] for i in hull(raw)]
            a, b = [(Fraction(rng.randrange(-10, 11)), Fraction(rng.randrange(-10, 11))) for _ in range(2)]
            if a == b:
                continue
            candidates = [p for p in polygon if cross(a, b, p) >= 0]
            for u, v in zip(polygon, polygon[1:]+polygon[:1]):
                cu, cv = cross(a, b, u), cross(a, b, v)
                if cu*cv < 0:
                    t = cu/(cu-cv)
                    candidates.append((u[0]+(v[0]-u[0])*t, u[1]+(v[1]-u[1])*t))
            expected = [candidates[i] for i in hull(candidates)]
            line = g.Line(g.Point(float(a[0]), float(a[1])), g.Point(float(b[0]), float(b[1])))
            for order in (polygon, polygon[::-1]):
                original = points(order)
                result = g.convex_cut(original, line)
                self.assertAlmostEqual(g.polygon_area(result), float(abs(area(expected))))
                for p in result:
                    self.assertTrue(any(hypot(p.x-float(q[0]), p.y-float(q[1])) < 1e-8 for q in candidates))
                for q in expected:
                    self.assertTrue(any(hypot(p.x-float(q[0]), p.y-float(q[1])) < 1e-8 for p in result))
                self.assertEqual([(p.x, p.y) for p in original], order)
                if g.polygon_area(result) > 1e-8:
                    self.assertEqual(g.polygon_signed_area(result) > 0, area(order) > 0)
        zero = g.Line(g.Point(1, 2), g.Point(1, 2))
        for polygon in ([], [g.Point(0, 0)]):
            with self.assertRaises(ValueError):
                g.convex_cut(polygon, zero)

    def test_closest_pair(self) -> None:
        rng = Random(0)
        for _ in range(1500):
            n = rng.randrange(2, 45)
            raw = [(rng.randrange(-20, 21)/4, rng.randrange(-20, 21)/4) for _ in range(n)]
            if rng.randrange(4) == 0:
                raw = [(x, 2*x) for x, _ in raw]
            values = [g.Point(x, y) for x, y in raw]
            before = values[:]
            expected = min(hypot(a.x-b.x, a.y-b.y) for a, b in combinations(values, 2))
            self.assertEqual(g.closest_pair_distance(values), expected)
            self.assertEqual([id(p) for p in values], [id(p) for p in before])
        for scale in (1e-200, 1e-12, 1.0, 1e100, 1e200):
            points = [g.Point(0, 0), g.Point(3*scale, 4*scale), g.Point(6*scale, 8*scale)]
            self.assertAlmostEqual(g.closest_pair_distance(points)/scale, 5.0)
            for _ in range(60):
                values = [g.Point(rng.uniform(-1, 1)*scale, rng.uniform(-1, 1)*scale) for _ in range(rng.randrange(2, 80))]
                expected = min(hypot(a.x-b.x, a.y-b.y) for a, b in combinations(values, 2))
                self.assertEqual(g.closest_pair_distance(values), expected)
        for values in ([], [g.Point(0, 0)]):
            with self.assertRaises(ValueError):
                g.closest_pair_distance(values)
        values = [g.Point(1, 2)]*10000
        self.assertEqual(g.closest_pair_distance(values), 0.0)
        # All x coordinates fit in the active strip of the old sweep, while
        # y order is scrambled, forcing costly list insertion/deletion.
        n = 5000
        ys = list(range(n))
        rng.shuffle(ys)
        values = [g.Point(i/n, 10*y) for i, y in enumerate(ys)]
        ordered = sorted(values, key=lambda p: p.y)
        expected = min(hypot(a.x-b.x, a.y-b.y) for a, b in zip(ordered, ordered[1:]))
        self.assertEqual(g.closest_pair_distance(values), expected)

    def test_koch_curve(self) -> None:
        start, end = g.Point(2, -3), g.Point(5, 1)
        previous = [start, end]
        for depth in range(6):
            result = g.koch_curve_points(start, end, depth)
            self.assertEqual(len(result), 4**depth+1)
            self.assertIs(result[0], start)
            self.assertIs(result[-1], end)
            for a, b in zip(result, result[1:]):
                self.assertAlmostEqual(hypot(a.x-b.x, a.y-b.y), 5/(3**depth))
            if depth:
                self.assertEqual(result[::4], previous)
            previous = result
        result = g.koch_curve_points(g.Point(0, 0), g.Point(3, 0), 1)
        expected = [(0, 0), (1, 0), (1.5, sqrt(3)/2), (2, 0), (3, 0)]
        for p, q in zip(result, expected):
            self.assertAlmostEqual(p.x, q[0])
            self.assertAlmostEqual(p.y, q[1])
        self.assertEqual(g.koch_curve_points(start, start, 3), [start]*(4**3+1))
        with self.assertRaises(ValueError):
            g.koch_curve_points(start, end, -1)


if __name__ == '__main__':
    unittest.main()
