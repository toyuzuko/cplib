from fractions import Fraction
from itertools import product
from math import hypot, inf, nan, pi, sqrt
from random import Random
import unittest
from unittest.mock import patch

from cplib.geometry import floating as g
from test.regression.test_geometry_exact_contracts import circle_through, enclosing_circle


class FloatingCircleContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.eps = g.get_eps()
        g.set_eps(1e-10)

    def tearDown(self) -> None:
        g.set_eps(self.eps)

    def assert_on_circle(self, point: g.Point, circle: g.Circle, delta: float = 1e-8) -> None:
        self.assertAlmostEqual(hypot(point.x-circle.center.x, point.y-circle.center.y), circle.radius, delta=delta)

    def test_triangle_circles_and_translations(self) -> None:
        rng = Random(0)
        cases = [[(0, 0), (2, 0), (0, 2)], [(0, 0), (4, 0), (0, 3)]]
        cases += [[(rng.randrange(-10, 11), rng.randrange(-10, 11)) for _ in range(3)] for _ in range(300)]
        for raw in cases:
            area2 = (raw[1][0]-raw[0][0])*(raw[2][1]-raw[0][1])-(raw[1][1]-raw[0][1])*(raw[2][0]-raw[0][0])
            for dx, dy in ((0, 0), (10**9, -10**9)):
                points = [g.Point(x+dx, y+dy) for x, y in raw]
                if not area2:
                    for solve in (g.triangle_incircle, g.triangle_circumcircle):
                        with self.assertRaises(ValueError):
                            solve(*points)
                    continue
                reference = tuple((Fraction(x+dx), Fraction(y+dy)) for x, y in raw)
                center, radius2 = circle_through(reference)
                for order in (points, list(reversed(points))):
                    actual = g.triangle_circumcircle(*order)
                    self.assertAlmostEqual(actual.center.x, float(center[0]), delta=5e-7)
                    self.assertAlmostEqual(actual.center.y, float(center[1]), delta=5e-7)
                    self.assertAlmostEqual(actual.radius, sqrt(float(radius2)), delta=1e-8)
                    for point in points:
                        self.assert_on_circle(point, actual, 5e-7)
                    incircle = g.triangle_incircle(*order)
                    perimeter = sum(hypot(a.x-b.x, a.y-b.y) for a, b in zip(points, points[1:]+points[:1]))
                    self.assertAlmostEqual(incircle.radius, abs(area2)/perimeter)
                    for a, b in zip(points, points[1:]+points[:1]):
                        distance = abs((b.x-a.x)*(incircle.center.y-a.y)-(b.y-a.y)*(incircle.center.x-a.x))/hypot(b.x-a.x,b.y-a.y)
                        self.assertAlmostEqual(distance, incircle.radius, delta=5e-7)
        g.set_eps(0.0)
        for scale in (1e-12, 1e-6, 1.0, 1e6):
            points = [g.Point(0, 0), g.Point(4*scale, 0), g.Point(0, 3*scale)]
            actual = g.triangle_incircle(*points)
            self.assertAlmostEqual(actual.center.x/scale, 1.0)
            self.assertAlmostEqual(actual.center.y/scale, 1.0)
            self.assertAlmostEqual(actual.radius/scale, 1.0)
            actual = g.triangle_circumcircle(*points)
            self.assertAlmostEqual(actual.center.x/scale, 2.0)
            self.assertAlmostEqual(actual.center.y/scale, 1.5)
            self.assertAlmostEqual(actual.radius/scale, 2.5)

    def test_circle_line_and_segment_intersections(self) -> None:
        rng = Random(0)
        for _ in range(1500):
            cx, cy, ax, ay, bx, by = [rng.randrange(-10, 11) for _ in range(6)]
            radius = rng.randrange(8)
            circle = g.Circle(g.Point(cx, cy), radius)
            line = g.Line(g.Point(ax, ay), g.Point(bx, by))
            segment = g.Segment(line.start, line.end)
            dx, dy = bx-ax, by-ay
            length2 = dx*dx+dy*dy
            if length2:
                t = Fraction((cx-ax)*dx+(cy-ay)*dy, length2)
                distance2 = Fraction((cx-ax)*dy-(cy-ay)*dx)**2/length2
                expected = distance2 <= radius*radius
                self.assertEqual(g.intersect_circle_line(circle, line), expected)
                if expected:
                    a, b = g.circle_line_cross_points(circle, line)
                    self.assertFalse(b < a)
                    for point in (a, b):
                        self.assert_on_circle(point, circle)
                        self.assertAlmostEqual((point.x-ax)*dy-(point.y-ay)*dx, 0.0, delta=1e-8)
                    if distance2 == radius*radius:
                        self.assertAlmostEqual(g.distance_pp(a, b), 0.0)
                else:
                    with self.assertRaises(ValueError):
                        g.circle_line_cross_points(circle, line)
                t = max(Fraction(0), min(Fraction(1), t))
            else:
                t = Fraction(0)
                with self.assertRaises(ValueError):
                    g.circle_line_cross_points(circle, line)
                with self.assertRaises(ValueError):
                    g.intersect_circle_line(circle, line)
            min_distance2 = (ax+t*dx-cx)**2+(ay+t*dy-cy)**2
            max_distance2 = max((ax-cx)**2+(ay-cy)**2, (bx-cx)**2+(by-cy)**2)
            self.assertEqual(g.intersect_circle_segment(circle, segment), min_distance2 <= radius*radius <= max_distance2)
        circle = g.Circle(g.Point(0, 0), 1.0)
        # A small nonzero line direction still defines an infinite line.
        result = g.circle_line_cross_points(circle, g.Line(g.Point(0, 0), g.Point(1e-12, 0)))
        self.assertEqual([(p.x, p.y) for p in result], [(-1.0, 0.0), (1.0, 0.0)])
        for gap, intersects in ((0.5e-10, True), (2e-10, False)):
            line = g.Line(g.Point(1+gap, 0), g.Point(1+gap, 1))
            self.assertEqual(g.intersect_circle_line(circle, line), intersects)
            if intersects:
                a, b = g.circle_line_cross_points(circle, line)
                self.assertEqual(a, b)
            else:
                with self.assertRaises(ValueError):
                    g.circle_line_cross_points(circle, line)

    def test_circle_pairs_and_degenerate_radii(self) -> None:
        rng = Random(0)
        cases = [(x, y, r, s) for x, y, r, s in product(range(4), range(3), range(4), range(4))]
        cases += [(rng.randrange(-10, 11), rng.randrange(-10, 11), rng.randrange(8), rng.randrange(8)) for _ in range(800)]
        for x, y, r, s in cases:
            first, second = g.Circle(g.Point(0, 0), r), g.Circle(g.Point(x, y), s)
            d2 = x*x+y*y
            if not d2:
                relation = 0
            elif d2 > (r+s)**2:
                relation = 4
            elif d2 == (r+s)**2:
                relation = 3
            elif d2 > (r-s)**2:
                relation = 2
            elif d2 == (r-s)**2:
                relation = 1
            else:
                relation = 0
            self.assertEqual(g.circle_relation(first, second), relation)
            self.assertEqual(g.circle_relation(second, first), relation)
            for a, b in ((first, second), (second, first)):
                if not d2 and r == s == 0:
                    answer = g.circle_circle_cross_points(a, b)
                    self.assertEqual(answer, (first.center, first.center))
                elif not d2 or not (r-s)**2 <= d2 <= (r+s)**2:
                    with self.assertRaises(ValueError):
                        g.circle_circle_cross_points(a, b)
                else:
                    p, q = g.circle_circle_cross_points(a, b)
                    self.assertFalse(q < p)
                    for point in (p, q):
                        self.assert_on_circle(point, a)
                        self.assert_on_circle(point, b)
        for radius in (-1.0, -inf, inf, nan):
            with self.assertRaises(ValueError):
                g.Circle(g.Point(0, 0), radius)
        g.set_eps(0.0)
        for scale in (1e-8, 1.0, 1e8):
            first, second = g.Circle(g.Point(0, 0), scale), g.Circle(g.Point(scale, 0), scale)
            p, q = g.circle_circle_cross_points(first, second)
            self.assertAlmostEqual(p.x/scale, 0.5)
            self.assertAlmostEqual(p.y/scale, -sqrt(3)/2)
            self.assertAlmostEqual(q.x/scale, 0.5)
            self.assertAlmostEqual(q.y/scale, sqrt(3)/2)

    def test_tangents(self) -> None:
        for r, s in ((0.0, 1e-12), (1e-12, 0.0), (1e-12, 1e-12)):
            self.assertEqual(g.common_tangent_points(g.Circle(g.Point(0, 0), r), g.Circle(g.Point(0, 0), s)), [])
        cases = list(product(range(-4, 5), range(-4, 5), range(5)))
        for x, y, r in cases:
            circle = g.Circle(g.Point(0, 0), r)
            query = g.Point(x, y)
            points = g.tangent_points_from_point(circle, query)
            count = 1 if r == 0 or x*x+y*y == r*r else 0 if x*x+y*y < r*r else 2
            self.assertEqual(len(points), count)
            self.assertEqual(points, sorted(points))
            for p in points:
                self.assert_on_circle(p, circle)
                self.assertAlmostEqual(p.x*(x-p.x)+p.y*(y-p.y), 0.0, delta=1e-8)
        for x, y, r, s in product(range(5), range(4), range(4), range(4)):
            first, second = g.Circle(g.Point(0, 0), r), g.Circle(g.Point(x, y), s)
            d2 = x*x+y*y
            if r == 0:
                count = int(d2 >= s*s)
            elif s == 0:
                count = 2 if d2 > r*r else 1 if d2 == r*r else 0
            elif d2 == 0:
                count = 0
            else:
                count = sum(2 if d2 > bound else 1 if d2 == bound else 0 for bound in ((r+s)**2, (r-s)**2))
            points = g.common_tangent_points(first, second)
            self.assertEqual(len(points), count, (x, y, r, s))
            self.assertEqual(points, sorted(points))
            for p in points:
                self.assert_on_circle(p, first)
                if r:
                    distance = abs((x-p.x)*p.x+(y-p.y)*p.y)/r
                    self.assertAlmostEqual(distance, s, delta=1e-8)
        g.set_eps(0.0)
        for scale in (1e-8, 1.0, 1e8):
            circle = g.Circle(g.Point(0, 0), scale)
            points = g.tangent_points_from_point(circle, g.Point(2*scale, 0))
            self.assertEqual(len(points), 2)
            self.assertAlmostEqual(points[0].x/scale, 0.5)
            self.assertAlmostEqual(abs(points[0].y)/scale, sqrt(3)/2)
            self.assertEqual(len(g.common_tangent_points(circle, g.Circle(g.Point(4*scale, 0), scale))), 4)

    def test_minimum_enclosing_circle(self) -> None:
        rng = Random(0)
        with patch.object(g, 'Random', return_value=Random(0)):
            for _ in range(220):
                raw = [(rng.randrange(-4, 5), rng.randrange(-4, 5)) for _ in range(rng.randrange(1, 9))]
                if rng.randrange(4) == 0:
                    raw = [(x, 2*x+1) for x, _ in raw]
                for dx, dy in ((0, 0), (10**9, -10**9)):
                    values = [(Fraction(x+dx), Fraction(y+dy)) for x, y in raw]
                    expected_center, radius2 = enclosing_circle(values)
                    points = [g.Point(float(x), float(y)) for x, y in values]
                    before = list(points)
                    actual = g.minimum_enclosing_circle(points)
                    self.assertAlmostEqual(actual.center.x, float(expected_center[0]), delta=5e-7)
                    self.assertAlmostEqual(actual.center.y, float(expected_center[1]), delta=5e-7)
                    self.assertAlmostEqual(actual.radius, sqrt(float(radius2)), delta=5e-7)
                    for p in points:
                        self.assertLessEqual(hypot(p.x-actual.center.x, p.y-actual.center.y), actual.radius+5e-7)
                    self.assertEqual([id(p) for p in points], [id(p) for p in before])
        with self.assertRaises(ValueError):
            g.minimum_enclosing_circle([])

    def test_circle_intersection_area(self) -> None:
        for scale in (1e-12, 1e-6, 1.0, 1e6):
            first = g.Circle(g.Point(0, 0), scale)
            for x, r, expected in ((0, 1, pi), (0, 0.5, pi/4), (0, 0, 0.0), (2, 1, 0.0), (3, 1, 0.0), (1, 1, 2*pi/3-sqrt(3)/2)):
                second = g.Circle(g.Point(x*scale, 0), r*scale)
                for eps in (0.0, 1e-10, 1.0):
                    g.set_eps(eps)
                    self.assertAlmostEqual(g.circle_circle_intersection_area(first, second)/(scale*scale), expected)
                    self.assertAlmostEqual(g.circle_circle_intersection_area(second, first)/(scale*scale), expected)
        rng = Random(0)
        # Composite midpoint quadrature of the vertical overlap height is
        # independent of the circular-segment formula used by the library.
        for _ in range(70):
            r, s = rng.randrange(1, 10), rng.randrange(1, 10)
            d = rng.randrange(1, 20)/2
            left, right = max(-r, d-s), min(r, d+s)
            n = 32768
            if left >= right:
                expected = 0.0
            else:
                step = (right-left)/n
                expected = step*sum(2*min(sqrt(max(0, r*r-(left+(i+0.5)*step)**2)), sqrt(max(0, s*s-(left+(i+0.5)*step-d)**2))) for i in range(n))
            first, second = g.Circle(g.Point(0, 0), r), g.Circle(g.Point(d, 0), s)
            actual = g.circle_circle_intersection_area(first, second)
            self.assertAlmostEqual(actual, expected, delta=5e-5)
            self.assertGreaterEqual(actual, 0.0)
            self.assertLessEqual(actual, pi*min(r, s)**2+1e-10)

    def test_circle_polygon_area(self) -> None:
        for scale in (1e-12, 1e-6, 1.0, 1e6):
            circle = g.Circle(g.Point(0, 0), scale)
            for raw, expected in (([(-2, -2), (2, -2), (2, 2), (-2, 2)], pi), ([(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)], 1.0), ([(0, 0), (2, 0), (2, 2), (0, 2)], pi/4), ([(0, -2), (2, -2), (2, 2), (0, 2)], pi/2), ([(2, 2), (3, 2), (3, 3), (2, 3)], 0.0)):
                polygon = [g.Point(x*scale, y*scale) for x, y in raw]
                for eps in (0.0, 1e-10, 1.0):
                    g.set_eps(eps)
                    for values in (polygon, list(reversed(polygon)), polygon+polygon[:1]):
                        actual = g.circle_polygon_intersection_area(circle, values)/(scale*scale)
                        self.assertAlmostEqual(actual, expected)
        rng = Random(0)
        for _ in range(100):
            radius = rng.randrange(1, 6)
            x1, x2 = sorted([rng.randrange(-10, 11)/2 for _ in range(2)])
            y1, y2 = sorted([rng.randrange(-10, 11)/2 for _ in range(2)])
            left, right = max(x1, -radius), min(x2, radius)
            n = 32768
            if left >= right:
                expected = 0.0
            else:
                step = (right-left)/n
                expected = 0.0
                for i in range(n):
                    x = left+(i+0.5)*step
                    h = sqrt(max(0, radius*radius-x*x))
                    expected += max(0.0, min(y2, h)-max(y1, -h))
                expected *= step
            polygon = [g.Point(x1, y1), g.Point(x2, y1), g.Point(x2, y2), g.Point(x1, y2)]
            actual = g.circle_polygon_intersection_area(g.Circle(g.Point(0, 0), radius), polygon)
            self.assertAlmostEqual(actual, expected, delta=2e-5)
        self.assertEqual(g.circle_polygon_intersection_area(g.Circle(g.Point(0, 0), 1), []), 0.0)
        self.assertEqual(g.circle_polygon_intersection_area(g.Circle(g.Point(0, 0), 0), [g.Point(-1, -1), g.Point(1, -1), g.Point(0, 1)]), 0.0)


if __name__ == '__main__':
    unittest.main()
