from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations, product
from math import atan2
from random import Random
import unittest
from unittest.mock import patch

from cplib.geometry import integer as gi, rational as gr
from cplib.mathematics.rational import Rational


Coord = tuple[Fraction, Fraction]
Circle = tuple[Coord, Fraction]


def coord(point: gr.Point) -> Coord:
    return Fraction(point.x.num, point.x.den), Fraction(point.y.num, point.y.den)


def squared(a: Coord, b: Coord) -> Fraction:
    return (a[0]-b[0])**2 + (a[1]-b[1])**2


def cross(a: Coord, b: Coord, c: Coord) -> Fraction:
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def circle_through(points: tuple[Coord, ...]) -> Circle:
    a = points[0]
    if len(points) == 1:
        return a, Fraction(0)
    b = points[1]
    if len(points) == 2 or cross(a, b, points[2]) == 0:
        a, b = max(combinations(points, 2), key=lambda pair: squared(*pair))
        center = ((a[0]+b[0])/2, (a[1]+b[1])/2)
    else:
        c = points[2]
        bx, by = b[0]-a[0], b[1]-a[1]
        cx, cy = c[0]-a[0], c[1]-a[1]
        ab, ac = squared(a, b)/2, squared(a, c)/2
        d = bx*cy-by*cx
        center = a[0]+(ab*cy-ac*by)/d, a[1]+(bx*ac-cx*ab)/d
    return center, squared(a, center)


def enclosing_circle(points: list[Coord]) -> Circle:
    if not points:
        return (Fraction(0), Fraction(0)), Fraction(0)
    candidates = (circle_through(group) for size in range(1, 4) for group in combinations(points, size))
    return min((circle for circle in candidates if all(squared(p, circle[0]) <= circle[1] for p in points)), key=lambda circle: circle[1])


def hull(points: list[Coord]) -> list[int]:
    unique = list(dict.fromkeys(points))
    if len(unique) <= 1:
        return [0] if points else []
    first = min(unique)
    result = [first]
    while True:
        a = result[-1]
        b = next(p for p in unique if p != a)
        for c in unique:
            turn = cross(a, b, c)
            if turn < 0 or turn == 0 and squared(a, c) > squared(a, b):
                b = c
        if b == first:
            break
        result.append(b)
    return [points.index(p) for p in result]


def on_segment(a: Coord, b: Coord, p: Coord) -> bool:
    return cross(a, b, p) == 0 and all(min(a[k], b[k]) <= p[k] <= max(a[k], b[k]) for k in range(2))


def segments_meet(a: Coord, b: Coord, c: Coord, d: Coord) -> bool:
    bx, by = b[0]-a[0], b[1]-a[1]
    dx, dy = d[0]-c[0], d[1]-c[1]
    determinant = bx*dy-by*dx
    if determinant == 0:
        return any((on_segment(a, b, c), on_segment(a, b, d), on_segment(c, d, a), on_segment(c, d, b)))
    cx, cy = c[0]-a[0], c[1]-a[1]
    t = (cx*dy-cy*dx)/determinant
    u = (cx*by-cy*bx)/determinant
    return 0 <= t <= 1 and 0 <= u <= 1


def integer_circle(circle: gi.Circle) -> Circle:
    return (Fraction(circle.center_num.x, circle.denominator), Fraction(circle.center_num.y, circle.denominator)), Fraction(circle.radius_squared_num, circle.denominator**2)


class ExactGeometryContractsTest(unittest.TestCase):
    def test_point_arithmetic_hash_and_angles(self) -> None:
        rng = Random(0)
        for _ in range(400):
            values = [Fraction(rng.randrange(-20, 21), rng.randrange(1, 10)) for _ in range(4)]
            x, y, u, v = values
            a, b = gr.Point(Rational(x.numerator, x.denominator), Rational(y.numerator, y.denominator)), gr.Point(Rational(u.numerator, u.denominator), Rational(v.numerator, v.denominator))
            self.assertEqual(coord(a+b), (x+u, y+v))
            self.assertEqual(coord(a-b), (x-u, y-v))
            self.assertEqual(coord(-a), (-x, -y))
            for actual, expected in ((a*b, x*u+y*v), (a@b, x*v-y*u), (gr.Point.dot(a, b), x*u+y*v), (gr.Point.cross(a, b), x*v-y*u), (gr.Point.squared_distance(a, b), (x-u)**2+(y-v)**2)):
                self.assertEqual(Fraction(actual.num, actual.den), expected)
            same = gr.Point(Rational(x.numerator*3, x.denominator*3, False), Rational(y.numerator*5, y.denominator*5, False))
            self.assertEqual(a, same)
            self.assertEqual(hash(a), hash(same))
        # Distinct diagonal points must not all collapse to the hash of 1/1.
        hashes = {hash(gr.Point(k, k)) for k in range(1000)}
        self.assertGreater(len(hashes), 900)
        for module in (gi, gr):
            points = [module.Point(x, y) for x, y in product(range(-5, 6), repeat=2)]
            points.extend([module.Point(0, 0), module.Point(2, 0), module.Point(1, 1)])
            rng.shuffle(points)
            original = list(points)
            ordered = module.argsort(points)
            expected = sorted(points, key=lambda p: atan2(p.y.num/p.y.den, p.x.num/p.x.den) if isinstance(p, gr.Point) else atan2(p.y, p.x))
            self.assertEqual([id(p) for p in ordered], [id(p) for p in expected])
            self.assertEqual([id(p) for p in points], [id(p) for p in original])
            self.assertEqual(module.argsort([]), [])

    def test_hulls_pairs_and_layers(self) -> None:
        rng = Random(0)
        for _ in range(240):
            raw = [(rng.randrange(-8, 9), rng.randrange(-8, 9)) for _ in range(rng.randrange(18))]
            if rng.randrange(4) == 0:
                raw = [(x, 2*x+1) for x, _ in raw]
            reference = [(Fraction(x), Fraction(y)) for x, y in raw]
            points = [gi.Point(x, y) for x, y in raw]
            expected = hull(reference)
            self.assertEqual(gi.convex_hull(points), expected)
            # An invertible positive scaling/translation preserves hull indices.
            fractions = [(x/3+Fraction(1, 7), y/5-Fraction(2, 9)) for x, y in reference]
            rational_points = [gr.Point(Rational(x.numerator, x.denominator), Rational(y.numerator, y.denominator)) for x, y in fractions]
            self.assertEqual(gr.convex_hull(rational_points), expected)
            if len(points) >= 2:
                distances = [squared(a, b) for a, b in combinations(reference, 2)]
                for solve, value in ((gi.closest_points, min(distances)), (gi.furthest_points, max(distances))):
                    i, j = solve(points)
                    self.assertNotEqual(i, j)
                    self.assertEqual(squared(reference[i], reference[j]), value)
            else:
                for solve in (gi.closest_points, gi.furthest_points):
                    with self.assertRaises(ValueError):
                        solve(points)
            unique = list(dict.fromkeys(raw))
            remaining = [(Fraction(x), Fraction(y)) for x, y in unique]
            original = remaining[:]
            expected_layers: dict[Coord, int] = {}
            level = 0
            while remaining:
                level += 1
                boundary = [remaining[i] for i in hull(remaining)]
                edges = list(zip(boundary, boundary[1:]+boundary[:1]))
                removed = [p for p in remaining if any(on_segment(a, b, p) for a, b in edges)]
                for p in removed:
                    expected_layers[p] = level
                remaining = [p for p in remaining if p not in expected_layers]
            self.assertEqual(gi.convex_layers([gi.Point(x, y) for x, y in unique]), [expected_layers[p] for p in original])
        with self.assertRaises(ValueError):
            gi.convex_layers([gi.Point(1, 2), gi.Point(1, 2)])
        big = 10**100
        for solve in (gi.closest_points, gi.furthest_points):
            self.assertEqual(set(solve([gi.Point(big, -big), gi.Point(-big, big)])), {0, 1})

    def test_segments_and_manhattan_pairs(self) -> None:
        raw = [(Fraction(x), Fraction(y)) for x, y in product(range(-1, 2), repeat=2)]
        pairs = list(product(raw, repeat=2))
        for a, b in pairs:
            first = gi.Segment(gi.Point(int(a[0]), int(a[1])), gi.Point(int(b[0]), int(b[1])))
            self.assertEqual(first, gi.Segment(first.end, first.start))
            self.assertAlmostEqual(first.length(), float(squared(a, b))**0.5)
            for p in raw:
                self.assertEqual(first.contains(gi.Point(int(p[0]), int(p[1]))), on_segment(a, b, p))
            for c, d in pairs:
                other = gi.Segment(gi.Point(int(c[0]), int(c[1])), gi.Point(int(d[0]), int(d[1])))
                self.assertEqual(first.intersects(other), segments_meet(a, b, c, d))
        rng = Random(0)
        for _ in range(150):
            coords: list[tuple[Coord, Coord]] = []
            for _ in range(rng.randrange(25)):
                x, y, z = [Fraction(rng.randrange(-3, 4)) for _ in range(3)]
                coords.append(((x, y), (x, z) if rng.randrange(2) else (z, y)))
            horizontal = [(a, b) for a, b in coords if a[1] == b[1]]
            vertical = [(a, b) for a, b in coords if a[1] != b[1]]
            expected = sum(segments_meet(a, b, c, d) for a, b in horizontal for c, d in vertical)
            segments = [gi.Segment(gi.Point(int(a[0]), int(a[1])), gi.Point(int(b[0]), int(b[1]))) for a, b in coords]
            self.assertEqual(gi.count_manhattan_intersections(segments), expected)
        with self.assertRaises(ValueError):
            gi.count_manhattan_intersections([gi.Segment(gi.Point(0, 0), gi.Point(1, 1))])
        for dy in (-3, 4):
            start, end = gr.Point(1, 2), gr.Point(1, 2+dy)
            s = gr.Segment(start=start, end=end)
            self.assertIs(s.start, start)
            self.assertIs(s.end, end)
            self.assertEqual(s.dir, end - start)
            self.assertEqual(s.slope, Rational(1 if dy > 0 else -1, 0))
        self.assertEqual(gr.Segment(gr.Point(1, 2), gr.Point(4, 4)).slope, Rational(2, 3))
        with self.assertRaises(ValueError):
            gr.Segment(gr.Point(1, 2), gr.Point(1, 2))

    def test_circle_construction_and_containment(self) -> None:
        rng = Random(0)
        for _ in range(400):
            raw = [(Fraction(rng.randrange(-8, 9)), Fraction(rng.randrange(-8, 9))) for _ in range(rng.randrange(1, 4))]
            expected = circle_through(tuple(raw))
            rational = gr.circumcircle([gr.Point(int(x), int(y)) for x, y in raw])
            self.assertEqual((coord(rational.center), Fraction(rational.radius_squared.num, rational.radius_squared.den)), expected)
            points = [gi.Point(int(x), int(y)) for x, y in raw]
            if len(points) == 1:
                integer = gi.Circle(points[0], 0)
            elif len(points) == 2:
                integer = gi.Circle.from_diameter(*points)
            else:
                integer = gi.Circle.from_three_points(*points)
            self.assertEqual(integer_circle(integer), expected)
            for _ in range(10):
                x, y = rng.randrange(-10, 11), rng.randrange(-10, 11)
                distance = squared((Fraction(x), Fraction(y)), expected[0])
                self.assertEqual(integer.contains(gi.Point(x, y)), distance <= expected[1])
                self.assertEqual(integer.on_circle(gi.Point(x, y)), distance == expected[1])
                self.assertEqual(rational.contains(gr.Point(x, y)), distance <= expected[1])
                self.assertEqual(rational.on_circle(gr.Point(x, y)), distance == expected[1])
            reversed_circle = gr.circumcircle([gr.Point(int(x), int(y)) for x, y in reversed(raw)])
            self.assertEqual(rational, reversed_circle)
        for points in ([], [gr.Point(0, 0)]*4):
            with self.assertRaises(ValueError):
                gr.circumcircle(points)
        with self.assertRaises(ValueError):
            gi.Circle(gi.Point(0, 0), -1)
        with self.assertRaises(ValueError):
            gr.Circle(gr.Point(0, 0), -1)
        with self.assertRaises(ValueError):
            gr.Circle.from_squared_radius(gr.Point(0, 0), Rational(-1, 3))
        half_center = gi.Circle.from_diameter(gi.Point(0, 0), gi.Point(1, 1))
        with self.assertRaises(ValueError):
            _ = half_center.center
        with self.assertRaises(ValueError):
            _ = half_center.radius
        irrational_radius = gi.Circle.from_diameter(gi.Point(0, 0), gi.Point(2, 2))
        self.assertEqual(irrational_radius.center, gi.Point(1, 1))
        with self.assertRaises(ValueError):
            _ = irrational_radius.radius
        integral = gi.Circle.from_diameter(gi.Point(-3, -4), gi.Point(3, 4))
        self.assertEqual((integral.center, integral.radius), (gi.Point(0, 0), 5))

    def test_disk_intersections(self) -> None:
        rng = Random(0)
        circles = [gi.Circle(gi.Point(x, y), r) for x, y, r in product(range(-2, 3), range(-2, 3), range(3))]
        circles += [gi.Circle.from_three_points(*(gi.Point(rng.randrange(-5, 6), rng.randrange(-5, 6)) for _ in range(3))) for _ in range(60)]
        circles += [gi.Circle.from_diameter(gi.Point(0, 0), gi.Point(1, 1)), gi.Circle.from_diameter(gi.Point(1, 1), gi.Point(2, 2))]
        with localcontext() as ctx:
            ctx.prec = 100
            def dec(x: Fraction) -> Decimal:
                return Decimal(x.numerator)/Decimal(x.denominator)
            for c1, c2 in product(circles, repeat=2):
                a, r2 = integer_circle(c1)
                b, s2 = integer_circle(c2)
                expected = dec(squared(a, b)).sqrt() <= dec(r2).sqrt()+dec(s2).sqrt()+Decimal('1e-80')
                self.assertEqual(c1.intersects(c2), expected)
        big = 10**100
        circle = gi.Circle(gi.Point(big, 0), big)
        self.assertTrue(circle.intersects(gi.Circle(gi.Point(-big, 0), big)))
        self.assertFalse(circle.intersects(gi.Circle(gi.Point(-big-1, 0), big)))

    def test_minimum_enclosing_circles(self) -> None:
        rng = Random(0)
        shuffle = Random(0).shuffle
        with patch.object(gi.random, 'shuffle', side_effect=shuffle):
            for _ in range(220):
                raw = [(Fraction(rng.randrange(-4, 5)), Fraction(rng.randrange(-4, 5))) for _ in range(rng.randrange(9))]
                if rng.randrange(4) == 0:
                    raw = [(x, 2*x+1) for x, _ in raw]
                center, radius2 = enclosing_circle(raw)
                flags = gi.minimum_enclosing_circle([gi.Point(int(x), int(y)) for x, y in raw])
                self.assertEqual(flags, [squared(p, center) == radius2 for p in raw])
                raw = [(x/Fraction(3)+Fraction(1, 7), y/Fraction(3)-Fraction(2, 9)) for x, y in raw]
                points = [gr.Point(Rational(x.numerator, x.denominator), Rational(y.numerator, y.denominator)) for x, y in raw]
                original = list(points)
                expected = enclosing_circle(raw)
                actual = gr.minimum_enclosing_circle(points)
                self.assertEqual((coord(actual.center), Fraction(actual.radius_squared.num, actual.radius_squared.den)), expected)
                self.assertEqual(points, original)


if __name__ == '__main__':
    unittest.main()
