from fractions import Fraction
from itertools import product
from math import hypot, inf, isnan, nan, sqrt
from random import Random
import unittest

from cplib.geometry import floating as g


Coord = tuple[Fraction, Fraction]


def point(a: Coord) -> g.Point:
    return g.Point(float(a[0]), float(a[1]))


def squared(a: Coord, b: Coord) -> Fraction:
    return (a[0]-b[0])**2+(a[1]-b[1])**2


def project(a: Coord, b: Coord, p: Coord, clamp: bool) -> Coord:
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = dx*dx+dy*dy
    if not length:
        return a
    t = ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length
    if clamp:
        t = max(Fraction(0), min(Fraction(1), t))
    return a[0]+t*dx, a[1]+t*dy


def on_segment(a: Coord, b: Coord, p: Coord) -> bool:
    return project(a, b, p, True) == p


def meet(a: Coord, b: Coord, c: Coord, d: Coord) -> bool:
    ux, uy = b[0]-a[0], b[1]-a[1]
    vx, vy = d[0]-c[0], d[1]-c[1]
    det = ux*vy-uy*vx
    if not det:
        return any((on_segment(a, b, c), on_segment(a, b, d), on_segment(c, d, a), on_segment(c, d, b)))
    px, py = c[0]-a[0], c[1]-a[1]
    t, s = (px*vy-py*vx)/det, (px*uy-py*ux)/det
    return 0 <= t <= 1 and 0 <= s <= 1


class FloatingGeometryPrimitivesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.eps = g.get_eps()
        g.set_eps(1e-10)

    def tearDown(self) -> None:
        g.set_eps(self.eps)

    def assert_point(self, actual: g.Point, expected: Coord) -> None:
        self.assertAlmostEqual(actual.x, float(expected[0]), delta=1e-9*max(1, abs(float(expected[0]))))
        self.assertAlmostEqual(actual.y, float(expected[1]), delta=1e-9*max(1, abs(float(expected[1]))))

    def test_tolerances_and_nonfinite_comparisons(self) -> None:
        for eps in (0.0, 1e-12, 1e-5, 1.0):
            g.set_eps(eps)
            self.assertEqual(g.get_eps(), eps)
            for x in (-2*eps, -eps, 0.0, eps, 2*eps, -inf, inf):
                self.assertEqual(g.sgn(x), (x > eps)-(x < -eps))
                self.assertEqual(g.equals(x, 0.0), -eps <= x <= eps)
            self.assertEqual(g.sgn(1e-7, 1e-6), 0)
            self.assertEqual(g.sgn(1e-7, 0.0), 1)
            self.assertEqual(g.get_eps(), eps)
            for bad in (-1.0, -1e-100, inf, -inf, nan):
                with self.assertRaises(ValueError):
                    g.set_eps(bad)
                self.assertEqual(g.get_eps(), eps)
                for compare in (g.sgn, lambda x, eps: g.equals(x, 0.0, eps)):
                    with self.assertRaises(ValueError):
                        compare(0.0, bad)
            with self.assertRaises(ValueError):
                g.sgn(nan)
            for a, b in product((0.0, 1.0, inf, -inf, nan), repeat=2):
                expected = False if isnan(a) or isnan(b) else a == b or -eps <= a-b <= eps
                self.assertEqual(g.equals(a, b), expected)
        self.assertFalse(g.Point(nan, 0.0) == g.Point(1.0, 0.0))
        self.assertFalse(g.Point(1.0, nan) == g.Point(1.0, 0.0))

    def test_point_operations_and_orientation(self) -> None:
        rng = Random(0)
        for _ in range(500):
            a, b, c = [(Fraction(rng.randrange(-100, 101)), Fraction(rng.randrange(-100, 101))) for _ in range(3)]
            p, q, r = point(a), point(b), point(c)
            self.assert_point(p+q, (a[0]+b[0], a[1]+b[1]))
            self.assert_point(p-q, (a[0]-b[0], a[1]-b[1]))
            self.assert_point(-p, (-a[0], -a[1]))
            self.assert_point(p.scale(0.25), (a[0]/4, a[1]/4))
            expected_dot = float(a[0]*b[0]+a[1]*b[1])
            expected_cross = float(a[0]*b[1]-a[1]*b[0])
            self.assertEqual((p*q, g.dot(p, q), g.Point.dot(p, q)), (expected_dot,)*3)
            self.assertEqual((p@q, g.cross(p, q), g.Point.cross(p, q)), (expected_cross,)*3)
            self.assertEqual(p.norm2(), a[0]**2+a[1]**2)
            self.assertEqual(g.norm2(p), p.norm2())
            self.assertEqual((p.abs(), g.abs(p)), (hypot(float(a[0]), float(a[1])),)*2)
            self.assertEqual(g.Point.squared_distance(p, q), squared(a, b))
            ux, uy = b[0]-a[0], b[1]-a[1]
            vx, vy = c[0]-a[0], c[1]-a[1]
            turn = ux*vy-uy*vx
            if turn:
                expected = g.COUNTER_CLOCKWISE if turn > 0 else g.CLOCKWISE
            elif ux*vx+uy*vy < 0:
                expected = g.ONLINE_BACK
            elif ux*ux+uy*uy < vx*vx+vy*vy:
                expected = g.ONLINE_FRONT
            else:
                expected = g.ON_SEGMENT
            self.assertEqual(g.ccw(p, q, r), expected)

    def test_lines_projection_reflection_and_distance(self) -> None:
        rng = Random(0)
        for _ in range(500):
            a, b, p = [(Fraction(rng.randrange(-100, 101)), Fraction(rng.randrange(-100, 101))) for _ in range(3)]
            if a == b:
                continue
            line = g.Line(point(a), point(b))
            segment = g.Segment(point(a), point(b))
            projection = project(a, b, p, False)
            nearest = project(a, b, p, True)
            self.assert_point(g.projection(line, point(p)), projection)
            self.assert_point(g.projection(segment, point(p)), projection)
            self.assert_point(g.reflection(line, point(p)), (2*projection[0]-p[0], 2*projection[1]-p[1]))
            distance_line = sqrt(float(squared(p, projection)))
            distance_segment = sqrt(float(squared(p, nearest)))
            self.assertAlmostEqual(g.distance_lp(line, point(p)), distance_line)
            self.assertAlmostEqual(g.distance_sp(segment, point(p)), distance_segment)
            self.assertAlmostEqual(g.distance(line, point(p)), distance_line)
            self.assertAlmostEqual(g.distance(point(p), line), distance_line)
            self.assertAlmostEqual(g.distance(segment, point(p)), distance_segment)
            self.assertAlmostEqual(g.distance(point(p), segment), distance_segment)
            self.assertAlmostEqual(g.distance(point(a), point(p)), sqrt(float(squared(a, p))))
            self.assert_point(line.direction(), (b[0]-a[0], b[1]-a[1]))
        zero_line = g.Line(g.Point(2.0, 3.0), g.Point(2.0, 3.0))
        for solve in (g.projection, g.reflection, g.distance_lp):
            with self.assertRaises(ValueError):
                solve(zero_line, g.Point(0.0, 0.0))
        with self.assertRaises(ValueError):
            g.cross_point(zero_line, zero_line)
        with self.assertRaises(TypeError):
            g.distance(zero_line, zero_line)
        # The segment endpoints remain distinct even when their separation
        # or squared length is smaller than EPS.
        for size in (1e-3, 1e-6, 1e-12):
            s = g.Segment(g.Point(0.0, 0.0), g.Point(size, 0.0))
            for x, y, expected in ((2*size, 0.0, size), (-size, 0.0, size), (size/2, size, size)):
                self.assertAlmostEqual(g.distance_sp(s, g.Point(x, y))/size, expected/size)
                reverse = g.Segment(s.end, s.start)
                self.assertAlmostEqual(g.distance_sp(reverse, g.Point(x, y))/size, expected/size)

    def test_segment_intersections_distances_and_degeneracy(self) -> None:
        coords = [(Fraction(x), Fraction(y)) for x, y in product(range(-1, 2), repeat=2)]
        segments = list(product(coords, repeat=2))
        for a, b in segments:
            first = g.Segment(point(a), point(b))
            for p in coords:
                self.assertEqual(first.contains(point(p)), on_segment(a, b, p))
            for c, d in segments:
                second = g.Segment(point(c), point(d))
                expected = meet(a, b, c, d)
                self.assertEqual(g.intersect(first, second), expected)
                if expected:
                    distance = 0.0
                else:
                    distance = sqrt(float(min(squared(p, project(u, v, p, True)) for u, v, p in ((a, b, c), (a, b, d), (c, d, a), (c, d, b)))))
                self.assertAlmostEqual(g.distance_ss(first, second), distance)
                self.assertAlmostEqual(g.distance(first, second), distance)
        for a in coords:
            first = g.Segment(point(a), point(a))
            for p in coords:
                self.assertAlmostEqual(g.distance_sp(first, point(p)), sqrt(float(squared(a, p))))
        g.set_eps(1e-10)
        zero = g.Segment(g.Point(0.0, 0.0), g.Point(0.0, 0.0))
        self.assertTrue(zero.contains(g.Point(1e-11, -1e-11)))
        self.assertFalse(zero.contains(g.Point(1e-6, 0.0)))
        self.assertFalse(g.intersect(zero, g.Segment(g.Point(1e-6, 0.0), g.Point(1e-6, 0.0))))

    def test_line_crossings_and_directions(self) -> None:
        rng = Random(0)
        for _ in range(500):
            a, b, c, d = [(Fraction(rng.randrange(-10, 11)), Fraction(rng.randrange(-10, 11))) for _ in range(4)]
            first, second = g.Line(point(a), point(b)), g.Line(point(c), point(d))
            ux, uy = b[0]-a[0], b[1]-a[1]
            vx, vy = d[0]-c[0], d[1]-c[1]
            determinant = ux*vy-uy*vx
            self.assertEqual(g.is_parallel(first, second), determinant == 0)
            self.assertEqual(g.is_orthogonal(first, second), ux*vx+uy*vy == 0)
            if determinant:
                t = ((c[0]-a[0])*vy-(c[1]-a[1])*vx)/determinant
                expected = a[0]+t*ux, a[1]+t*uy
                self.assert_point(g.cross_point(first, second), expected)
                self.assert_point(g.cross_point(second, first), expected)
            else:
                with self.assertRaises(ValueError):
                    g.cross_point(first, second)


if __name__ == '__main__':
    unittest.main()
