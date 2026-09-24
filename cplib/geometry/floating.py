#!/usr/bin/env python3

from __future__ import annotations

from math import acos, atan2, hypot, isfinite, pi, sin, sqrt
from random import Random
from typing import TypeAlias


EPS = 1e-10

COUNTER_CLOCKWISE = 1
CLOCKWISE = -1
ONLINE_BACK = 2
ONLINE_FRONT = -2
ON_SEGMENT = 0

POINT_OUTSIDE_POLYGON = 0
POINT_ON_POLYGON = 1
POINT_INSIDE_POLYGON = 2


def set_eps(eps: float) -> None:
    """Set the module-wide tolerance for floating-point geometry.

    Args:
        eps: Finite, non-negative absolute tolerance. Zero requests exact
            scalar comparisons. Geometric predicates apply this tolerance
            to their scalar expressions (including dot/cross products), not
            uniformly to Euclidean distances.

    Returns:
        None.

    Raises:
        ValueError: If eps is negative or non-finite. The setting is unchanged.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    if not isfinite(eps) or eps < 0.0:
        raise ValueError('eps must be finite and non-negative')
    globals()['EPS'] = float(eps)


def get_eps() -> float:
    """Return the current module-wide floating-point tolerance.

    Args:
        None.

    Returns:
        Current tolerance.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return float(EPS)


def sgn(x: float, eps: float | None = None) -> int:
    """Return the sign of ``x`` under a tolerance.

    Args:
        x: Value to classify; signed infinities are allowed, NaN is not.
        eps: Finite, non-negative tolerance. If omitted, ``EPS`` is used.

    Returns:
        1 if x > eps, -1 if x < -eps, and 0 when -eps <= x <= eps.

    Raises:
        ValueError: If x is NaN or the specified eps is negative or non-finite.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    if eps is None:
        eps = EPS
    elif not isfinite(eps) or eps < 0.0:
        raise ValueError('eps must be finite and non-negative')
    if x > eps:
        return 1
    if x < -eps:
        return -1
    if x != x:
        raise ValueError('cannot classify NaN')
    return 0


def equals(a: float, b: float, eps: float | None = None) -> bool:
    """Return whether two floating-point values are equal under tolerance.

    Args:
        a: First value.
        b: Second value.
        eps: Finite, non-negative tolerance. If omitted, ``EPS`` is used.

    Returns:
        True if a and b are equal or differ by at most eps. Equal signed
        infinities compare equal; NaN compares unequal to every value.

    Raises:
        ValueError: If the specified eps is negative or non-finite.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    if eps is None:
        eps = EPS
    elif not isfinite(eps) or eps < 0.0:
        raise ValueError('eps must be finite and non-negative')
    return a == b or -eps <= a - b <= eps


class Point:
    """2D point or vector with floating-point coordinates.

    Attributes:
        x: Finite x-coordinate for geometric algorithms.
        y: Finite y-coordinate for geometric algorithms.

    Space Complexity:
        O(1)
    """

    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float) -> None:
        """Initialize a point.

        Args:
            x: X-coordinate.
            y: Y-coordinate.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.x = float(x)
        self.y = float(y)

    def __add__(self, other: 'Point') -> 'Point':
        """Return vector addition.

        Args:
            other: Point to add.

        Returns:
            Sum of the two vectors.
        """
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point') -> 'Point':
        """Return vector subtraction.

        Args:
            other: Point to subtract.

        Returns:
            Difference of the two vectors.
        """
        return Point(self.x - other.x, self.y - other.y)

    def __neg__(self) -> 'Point':
        """Return the negated vector.

        Args:
            None.

        Returns:
            Negated vector.
        """
        return Point(-self.x, -self.y)

    def __eq__(self, other: object) -> bool:
        """Return whether two points are equal under ``EPS``.

        Args:
            other: Object to compare.

        Returns:
            True if both coordinates are equal under tolerance.
        """
        if not isinstance(other, Point):
            return NotImplemented
        return equals(self.x, other.x) and equals(self.y, other.y)

    def __lt__(self, other: 'Point') -> bool:
        """Return lexicographic comparison under exact float ordering.

        Args:
            other: Point to compare with.

        Returns:
            True if this point is lexicographically smaller.
        """
        if self.x != other.x:
            return self.x < other.x
        return self.y < other.y

    def __mul__(self, other: 'Point') -> float:
        """Return the dot product.

        Args:
            other: Vector to multiply with.

        Returns:
            Dot product.
        """
        return self.x * other.x + self.y * other.y

    def __matmul__(self, other: 'Point') -> float:
        """Return the cross product.

        Args:
            other: Vector to multiply with.

        Returns:
            Signed 2D cross product.
        """
        return self.x * other.y - self.y * other.x

    def scale(self, k: float) -> 'Point':
        """Return this vector multiplied by a scalar.

        Args:
            k: Scalar multiplier.

        Returns:
            Scaled vector.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return Point(self.x * k, self.y * k)

    def norm2(self) -> float:
        """Return the squared Euclidean norm.

        Args:
            None.

        Returns:
            Squared norm.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return self.x * self.x + self.y * self.y

    def abs(self) -> float:
        """Return the Euclidean norm.

        Args:
            None.

        Returns:
            Euclidean norm.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return hypot(self.x, self.y)

    @staticmethod
    def dot(p1: 'Point', p2: 'Point') -> float:
        """Return the dot product of two vectors.

        Args:
            p1: First vector.
            p2: Second vector.

        Returns:
            Dot product.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return p1.x * p2.x + p1.y * p2.y

    @staticmethod
    def cross(p1: 'Point', p2: 'Point') -> float:
        """Return the cross product of two vectors.

        Args:
            p1: First vector.
            p2: Second vector.

        Returns:
            Signed 2D cross product.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return p1.x * p2.y - p1.y * p2.x

    @staticmethod
    def squared_distance(p1: 'Point', p2: 'Point') -> float:
        """Return the squared distance between two points.

        Args:
            p1: First point.
            p2: Second point.

        Returns:
            Squared Euclidean distance.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return (p1 - p2).norm2()


class Line:
    """Directed line represented by two points.

    Attributes:
        start: First point on the line.
        end: Second point on the line.

    Notes:
        Operations on the supporting infinite line require distinct
        endpoints. Segment subclasses may have coincident endpoints and
        then represent a single point.

    Space Complexity:
        O(1)
    """

    __slots__ = ('start', 'end')

    def __init__(self, start: Point, end: Point) -> None:
        """Initialize a directed line.

        Args:
            start: First point on the line.
            end: Second point on the line.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.start = start
        self.end = end

    def direction(self) -> Point:
        """Return the direction vector.

        Args:
            None.

        Returns:
            ``end - start``.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        return self.end - self.start


class Segment(Line):
    """Line segment represented by two endpoints.

    Attributes:
        start: First endpoint.
        end: Second endpoint.

    Space Complexity:
        O(1)
    """

    def contains(self, point: Point) -> bool:
        """Return whether a point lies on this segment.

        Args:
            point: Point to test.

        Returns:
            True if the point is on the segment under ``EPS``. For coincident
            endpoints, use coordinate-wise point equality under ``EPS``.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)
        """
        if self.start.x == self.end.x and self.start.y == self.end.y:
            return point == self.start
        return ccw(self.start, self.end, point) == ON_SEGMENT


class Circle:
    """Circle with floating-point center and radius.

    Attributes:
        center: Center point.
        radius: Radius.

    Space Complexity:
        O(1)
    """

    __slots__ = ('center', 'radius')

    def __init__(self, center: Point, radius: float) -> None:
        """Initialize a circle.

        Args:
            center: Center point.
            radius: Finite, non-negative radius.

        Returns:
            None.

        Raises:
            ValueError: If radius is negative or non-finite.

        Time Complexity:
            O(1)
        """
        if not isfinite(radius) or radius < 0.0:
            raise ValueError('radius must be finite and non-negative')
        self.center = center
        self.radius = float(radius)


LineLike: TypeAlias = Line | Segment


def dot(p1: Point, p2: Point) -> float:
    """Return the dot product of two vectors.

    Args:
        p1: First vector.
        p2: Second vector.

    Returns:
        Dot product.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return Point.dot(p1, p2)


def cross(p1: Point, p2: Point) -> float:
    """Return the cross product of two vectors.

    Args:
        p1: First vector.
        p2: Second vector.

    Returns:
        Signed 2D cross product.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return Point.cross(p1, p2)


def norm2(p: Point) -> float:
    """Return the squared Euclidean norm of a vector.

    Args:
        p: Input vector.

    Returns:
        Squared norm.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return p.norm2()


def abs(p: Point) -> float:
    """Return the Euclidean norm of a vector.

    Args:
        p: Input vector.

    Returns:
        Euclidean norm.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return p.abs()


def ccw(a: Point, b: Point, c: Point) -> int:
    """Classify the position of ``c`` against directed segment ``a-b``.

    Args:
        a: Segment start.
        b: Segment end.
        c: Query point.

    Returns:
        ``COUNTER_CLOCKWISE``, ``CLOCKWISE``, ``ONLINE_BACK``,
        ``ONLINE_FRONT``, or ``ON_SEGMENT``.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    ab = b - a
    ac = c - a
    cr = cross(ab, ac)
    cr_sign = sgn(cr)
    if cr_sign > 0:
        return COUNTER_CLOCKWISE
    if cr_sign < 0:
        return CLOCKWISE
    if sgn(dot(ab, ac)) < 0:
        return ONLINE_BACK
    if sgn(norm2(ab) - norm2(ac)) < 0:
        return ONLINE_FRONT
    return ON_SEGMENT


def is_parallel(line1: LineLike, line2: LineLike) -> bool:
    """Return whether two lines are parallel.

    Args:
        line1: First line or segment.
        line2: Second line or segment.

    Returns:
        True if their direction vectors have cross product zero under EPS.
        A zero direction therefore returns True; this does not define a
        supporting line for coincident endpoints.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return sgn(cross(line1.direction(), line2.direction())) == 0


def is_orthogonal(line1: LineLike, line2: LineLike) -> bool:
    """Return whether two lines are orthogonal.

    Args:
        line1: First line or segment.
        line2: Second line or segment.

    Returns:
        True if their direction vectors have dot product zero under EPS.
        A zero direction therefore returns True; this does not define a
        supporting line for coincident endpoints.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return sgn(dot(line1.direction(), line2.direction())) == 0


def projection(line: LineLike, point: Point) -> Point:
    """Return the orthogonal projection of a point onto a line.

    Args:
        line: Target line or segment, treated as an infinite line.
        point: Point to project.

    Returns:
        Projected point on the line.

    Raises:
        ValueError: If ``line`` has zero length.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    base = line.direction()
    denom = norm2(base)
    if denom == 0.0:
        raise ValueError('line endpoints must be distinct')
    return line.start + base.scale(dot(point - line.start, base) / denom)


def reflection(line: LineLike, point: Point) -> Point:
    """Return the reflection of a point across a line.

    Args:
        line: Mirror line or segment, treated as an infinite line.
        point: Point to reflect.

    Returns:
        Reflected point.

    Raises:
        ValueError: If the line endpoints coincide.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    p = projection(line, point)
    return point + (p - point).scale(2.0)


def intersect(segment1: Segment, segment2: Segment) -> bool:
    """Return whether two segments intersect.

    Args:
        segment1: First segment.
        segment2: Second segment.

    Returns:
        True if the two segments have at least one common point under EPS.
        Endpoints are included, and zero-length segments are treated as points.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    if segment1.start.x == segment1.end.x and segment1.start.y == segment1.end.y:
        return segment2.contains(segment1.start)
    if segment2.start.x == segment2.end.x and segment2.start.y == segment2.end.y:
        return segment1.contains(segment2.start)
    c1 = ccw(segment1.start, segment1.end, segment2.start)
    c2 = ccw(segment1.start, segment1.end, segment2.end)
    c3 = ccw(segment2.start, segment2.end, segment1.start)
    c4 = ccw(segment2.start, segment2.end, segment1.end)
    return c1 * c2 <= 0 and c3 * c4 <= 0


def cross_point(line1: LineLike, line2: LineLike) -> Point:
    """Return the intersection point of two non-parallel lines.

    Args:
        line1: First line or segment.
        line2: Second line or segment.

    Returns:
        Intersection point of the supporting lines.

    Raises:
        ValueError: If the two supporting lines are parallel.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    base1 = line1.direction()
    base2 = line2.direction()
    denom = cross(base1, base2)
    if sgn(denom) == 0:
        raise ValueError('lines must not be parallel')
    ratio = cross(line2.start - line1.start, base2) / denom
    return line1.start + base1.scale(ratio)


def distance_pp(point1: Point, point2: Point) -> float:
    """Return the distance between two points.

    Args:
        point1: First point.
        point2: Second point.

    Returns:
        Euclidean distance.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return (point1 - point2).abs()


def distance_lp(line: LineLike, point: Point) -> float:
    """Return the distance from a point to a line.

    Args:
        line: Target line or segment, treated as an infinite line.
        point: Query point.

    Returns:
        Euclidean distance to the supporting line.

    Raises:
        ValueError: If the line endpoints coincide.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return distance_pp(point, projection(line, point))


def distance_sp(segment: Segment, point: Point) -> float:
    """Return the distance from a point to a segment.

    Args:
        segment: Target segment.
        point: Query point.

    Returns:
        Euclidean distance to the closed segment. Coincident endpoints are
        treated as a point. Projection is clamped to the segment using exact
        float comparisons rather than EPS, so tiny segments are not extended.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    direction = segment.direction()
    length_squared = direction.norm2()
    along = dot(direction, point - segment.start)
    if length_squared == 0.0 or along <= 0.0:
        return distance_pp(segment.start, point)
    if along >= length_squared:
        return distance_pp(segment.end, point)
    return distance_pp(segment.start + direction.scale(along / length_squared), point)


def distance_ss(segment1: Segment, segment2: Segment) -> float:
    """Return the distance between two segments.

    Args:
        segment1: First segment.
        segment2: Second segment.

    Returns:
        Euclidean distance between the segments, or zero if intersect reports
        an intersection under EPS. Zero-length segments are supported.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    if intersect(segment1, segment2):
        return 0.0
    return min(
        distance_sp(segment1, segment2.start),
        distance_sp(segment1, segment2.end),
        distance_sp(segment2, segment1.start),
        distance_sp(segment2, segment1.end),
    )


def distance(obj1: Point | LineLike, obj2: Point | LineLike) -> float:
    """Return the Euclidean distance between supported geometry objects.

    Args:
        obj1: A point, line, or segment.
        obj2: A point, line, or segment.

    Returns:
        Euclidean distance. Lines are only supported with points.

    Raises:
        TypeError: If the argument combination is unsupported.
        ValueError: If a Line argument has coincident endpoints. Zero-length
            Segment arguments are supported as points.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    if isinstance(obj1, Point) and isinstance(obj2, Point):
        return distance_pp(obj1, obj2)
    if isinstance(obj1, Segment) and isinstance(obj2, Segment):
        return distance_ss(obj1, obj2)
    if isinstance(obj1, Segment) and isinstance(obj2, Point):
        return distance_sp(obj1, obj2)
    if isinstance(obj1, Point) and isinstance(obj2, Segment):
        return distance_sp(obj2, obj1)
    if isinstance(obj1, Line) and isinstance(obj2, Point):
        return distance_lp(obj1, obj2)
    if isinstance(obj1, Point) and isinstance(obj2, Line):
        return distance_lp(obj2, obj1)
    raise TypeError('unsupported geometry object combination')


def circle_relation(circle1: Circle, circle2: Circle) -> int:
    """Classify the positional relationship of two circles.

    Args:
        circle1: First circle.
        circle2: Second circle.

    Returns:
        4 if separate, 3 if externally tangent, 2 if crossing at two points,
        1 if internally tangent, and 0 if one contains the other. Concentric
        circles, including coincident circles, return 0. Other comparisons
        use EPS on distances. A point-circle contact returns 3 when external
        and internal tangency coincide.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    d = distance_pp(circle1.center, circle2.center)
    if d == 0.0:
        return 0
    rsum = circle1.radius + circle2.radius
    rdiff = circle1.radius - circle2.radius
    if rdiff < 0.0:
        rdiff = -rdiff
    if sgn(d - rsum) > 0:
        return 4
    if sgn(d - rsum) == 0:
        return 3
    if sgn(d - rdiff) > 0:
        return 2
    if sgn(d - rdiff) == 0:
        return 1
    return 0


def triangle_incircle(a: Point, b: Point, c: Point) -> Circle:
    """Return the incircle of a triangle.

    Args:
        a: First vertex.
        b: Second vertex.
        c: Third vertex.

    Returns:
        The incircle.

    Raises:
        ValueError: If the vertices are collinear under EPS on their cross
            product, including repeated vertices.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    ab = b - a
    ac = c - a
    twice_area = cross(ab, ac)
    if sgn(twice_area) == 0:
        raise ValueError('triangle must be non-degenerate')
    la = distance_pp(b, c)
    lb = ac.abs()
    lc = ab.abs()
    perimeter = la + lb + lc
    center = a + (ab.scale(lb) + ac.scale(lc)).scale(1.0 / perimeter)
    radius = twice_area / perimeter
    if radius < 0.0:
        radius = -radius
    return Circle(center, radius)


def triangle_circumcircle(a: Point, b: Point, c: Point) -> Circle:
    """Return the circumcircle of a triangle.

    Args:
        a: First vertex.
        b: Second vertex.
        c: Third vertex.

    Returns:
        The circumcircle, computed from coordinate differences to reduce
        cancellation after a large translation.

    Raises:
        ValueError: If the vertices are collinear under EPS on their cross
            product, including repeated vertices.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    ab = b - a
    ac = c - a
    twice_area = cross(ab, ac)
    if sgn(twice_area) == 0:
        raise ValueError('triangle must be non-degenerate')
    d = 2.0 * twice_area
    bb = ab.norm2()
    cc = ac.norm2()
    offset = Point(
        (bb * ac.y - cc * ab.y) / d,
        (cc * ab.x - bb * ac.x) / d,
    )
    return Circle(a + offset, offset.abs())


def intersect_circle_line(circle: Circle, line: LineLike) -> bool:
    """Return whether a circle and an infinite line intersect.

    Args:
        circle: Circle to test.
        line: Line to test.

    Returns:
        True if the circle circumference and the line have a common point.

    Raises:
        ValueError: If the line endpoints coincide.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    return sgn(distance_lp(line, circle.center) - circle.radius) <= 0


def intersect_circle_segment(circle: Circle, segment: Segment) -> bool:
    """Return whether a circle and a segment intersect.

    Args:
        circle: Circle to test.
        segment: Segment to test.

    Returns:
        True if the circle circumference and the segment have a common point
        under EPS. A segment wholly inside the disk returns False. Zero-length
        segments and zero-radius circles are supported.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    if sgn(distance_sp(segment, circle.center) - circle.radius) > 0:
        return False
    return (
        sgn(distance_pp(circle.center, segment.start) - circle.radius) >= 0
        or sgn(distance_pp(circle.center, segment.end) - circle.radius) >= 0
    )


def circle_line_cross_points(circle: Circle, line: LineLike) -> tuple[Point, Point]:
    """Return the intersection points of a circle and an infinite line.

    Args:
        circle: Circle to intersect.
        line: Line to intersect.

    Returns:
        Two intersection points sorted lexicographically. Tangency returns the
        same point twice. Gaps no larger than EPS are treated as tangency.

    Raises:
        ValueError: If the line endpoints coincide or the line misses the
            circle by more than EPS.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    foot = projection(line, circle.center)
    direction = line.direction()
    length = direction.abs()
    if length == 0.0:
        raise ValueError('line direction must be non-zero')
    distance = distance_pp(foot, circle.center)
    if sgn(distance - circle.radius) > 0:
        raise ValueError('line does not intersect circle')
    h2 = (circle.radius - distance) * (circle.radius + distance)
    h = sqrt(max(0.0, h2))
    unit = direction.scale(1.0 / length)
    p1 = foot - unit.scale(h)
    p2 = foot + unit.scale(h)
    return (p1, p2) if p1 < p2 else (p2, p1)


def circle_circle_cross_points(circle1: Circle, circle2: Circle) -> tuple[Point, Point]:
    """Return the intersection points of two circles.

    Args:
        circle1: First circle.
        circle2: Second circle.

    Returns:
        Two intersection points sorted lexicographically. Tangency returns the
        same point twice. Two coincident zero-radius circles return their
        center twice. Gaps no larger than EPS are treated as tangency.

    Raises:
        ValueError: If the circumferences do not meet under EPS, or coincident
            positive-radius circles have infinitely many intersection points.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    vector = circle2.center - circle1.center
    d = vector.abs()
    r1, r2 = circle1.radius, circle2.radius
    if d == 0.0:
        if r1 == r2 == 0.0:
            return circle1.center, circle1.center
        raise ValueError('concentric circles do not have one or two intersection points')
    difference = r1 - r2
    radius_gap = difference if difference >= 0.0 else -difference
    if sgn(d - (r1 + r2)) > 0 or sgn(d - radius_gap) < 0:
        raise ValueError('circle circumferences do not intersect')
    unit = vector.scale(1.0 / d)
    a = (difference * (r1 + r2) + d * d) / (2.0 * d)
    h2 = (r1 - a) * (r1 + a)
    h = sqrt(max(0.0, h2))
    base = circle1.center + unit.scale(a)
    normal = Point(-unit.y, unit.x).scale(h)
    p1 = base - normal
    p2 = base + normal
    return (p1, p2) if p1 < p2 else (p2, p1)


def tangent_points_from_point(circle: Circle, point: Point) -> list[Point]:
    """Return tangent points from an external point to a circle.

    Args:
        circle: Circle to touch.
        point: Query point.

    Returns:
        Two tangent points sorted lexicographically for an external point,
        one point for a boundary point under EPS, or [] for an interior point.
        A zero-radius circle returns its center once.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    vector = point - circle.center
    d = vector.abs()
    r = circle.radius
    if r == 0.0:
        return [circle.center]
    relation = sgn(d - r)
    if relation < 0:
        return []
    if relation == 0:
        return [point]
    unit = vector.scale(1.0 / d)
    cosine = r / d
    base = circle.center + unit.scale(r * cosine)
    h = r * sqrt(max(0.0, (1.0 - cosine) * (1.0 + cosine)))
    normal = Point(-unit.y, unit.x).scale(h)
    p1 = base - normal
    p2 = base + normal
    return [p1, p2] if p1 < p2 else [p2, p1]


def common_tangent_points(circle1: Circle, circle2: Circle) -> list[Point]:
    """Return tangent points on the first circle for common tangents.

    Args:
        circle1: First circle.
        circle2: Second circle.

    Returns:
        Points on ``circle1`` touched by common tangents, sorted
        lexicographically and deduplicated under EPS. Concentric circles with
        a positive radius return [] (coincident circles have no isolated
        tangent points to enumerate). Zero-radius circles are supported.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    vector = circle2.center - circle1.center
    d = vector.abs()
    if d == 0.0:
        return [circle1.center] if circle1.radius == circle2.radius == 0.0 else []
    if circle1.radius == 0.0:
        return [circle1.center] if sgn(d - circle2.radius) >= 0 else []
    if circle2.radius == 0.0:
        return tangent_points_from_point(circle1, circle2.center)
    unit = vector.scale(1.0 / d)
    points: list[Point] = []
    for sign in (-1.0, 1.0):
        r = circle1.radius - sign * circle2.radius
        radius_gap = r if r >= 0.0 else -r
        relation = sgn(d - radius_gap)
        if relation < 0:
            continue
        cosine = r / d
        sine = sqrt(max(0.0, (1.0 - cosine) * (1.0 + cosine)))
        roots = [0.0] if relation == 0 else [-sine, sine]
        for h in roots:
            direction = Point(
                unit.x * cosine - unit.y * h,
                unit.y * cosine + unit.x * h,
            )
            points.append(circle1.center + direction.scale(circle1.radius))

    points.sort()
    unique: list[Point] = []
    for point in points:
        if not unique or point != unique[-1]:
            unique.append(point)
    return unique


def polygon_signed_area(points: list[Point]) -> float:
    """Return the signed area of a polygon.

    Args:
        points: Polygon vertices in cyclic order.

    Returns:
        Signed area, positive for counter-clockwise vertex order. Fewer than
        three vertices gives zero. Coordinates are translated to the first
        vertex before multiplication to reduce cancellation. The first vertex
        may also be repeated at the end.

    Time Complexity:
        O(n)

    Space Complexity:
        O(1)
    """
    n = len(points)
    if n < 3:
        return 0.0
    x0, y0 = points[0].x, points[0].y
    area2 = 0.0
    for i in range(1, n - 1):
        area2 += (points[i].x - x0) * (points[i + 1].y - y0) - (points[i].y - y0) * (points[i + 1].x - x0)
    return area2 * 0.5


def polygon_area(points: list[Point]) -> float:
    """Return the area of a polygon.

    Args:
        points: Polygon vertices in cyclic order.

    Returns:
        Non-negative polygon area.

    Time Complexity:
        O(n)

    Space Complexity:
        O(1)
    """
    area = polygon_signed_area(points)
    return area if area >= 0.0 else -area


def is_convex_polygon(points: list[Point], allow_collinear: bool = True) -> bool:
    """Return whether a polygon is convex.

    Args:
        points: Vertices of a simple polygon in cyclic order, without repeating
            the first vertex at the end or consecutive duplicate vertices.
            Self-intersections are not checked.
        allow_collinear: Whether 180-degree angles are allowed.

    Returns:
        True if all nonzero turns have a consistent orientation under EPS,
        and at least one turn is nonzero. Empty, singleton, two-vertex, and
        entirely collinear inputs return False.

    Time Complexity:
        O(n)

    Space Complexity:
        O(1)
    """
    n = len(points)
    if n < 3:
        return False
    direction = 0
    for i in range(n):
        turn = sgn(cross(points[(i + 1) % n] - points[i], points[(i + 2) % n] - points[(i + 1) % n]))
        if turn == 0:
            if not allow_collinear:
                return False
            continue
        if direction == 0:
            direction = turn
        elif direction != turn:
            return False
    return direction != 0


def contains_point_in_polygon(points: list[Point], point: Point) -> int:
    """Classify a point against a polygon.

    Args:
        points: Simple polygon vertices in cyclic order. Repeated consecutive
            vertices and a repeated closing vertex are allowed.
        point: Query point.

    Returns:
        ``POINT_INSIDE_POLYGON`` if inside, ``POINT_ON_POLYGON`` if on the
        boundary, and ``POINT_OUTSIDE_POLYGON`` otherwise. Empty input is
        outside. One vertex is treated as a point and two as a segment.

    Time Complexity:
        O(n)

    Space Complexity:
        O(1)
    """
    n = len(points)
    inside = False
    for i in range(n):
        if points[i].x == points[(i + 1) % n].x and points[i].y == points[(i + 1) % n].y:
            if points[i] == point:
                return POINT_ON_POLYGON
            continue
        a = points[i] - point
        b = points[(i + 1) % n] - point
        if sgn(cross(a, b)) == 0 and sgn(dot(a, b)) <= 0:
            return POINT_ON_POLYGON
        if a.y > b.y:
            a, b = b, a
        if sgn(a.y) <= 0 and sgn(b.y) > 0 and sgn(cross(a, b)) > 0:
            inside = not inside
    return POINT_INSIDE_POLYGON if inside else POINT_OUTSIDE_POLYGON


def convex_hull(points: list[Point], keep_collinear: bool = False) -> list[Point]:
    """Return the convex hull of a point set.

    Args:
        points: Input points; the list is not reordered.
        keep_collinear: Whether to keep collinear boundary points.

    Returns:
        Convex hull vertices in counter-clockwise order, starting from the
        lexicographically smallest point, without repeating it at the end.
        Empty input gives []. A collinear set gives its extremes, or all
        sorted points when keep_collinear is True. Consecutive points in
        lexicographic order are deduplicated using coordinate-wise EPS;
        turns use EPS on cross products. Returned points are input objects.

    Time Complexity:
        O(n log n)

    Space Complexity:
        O(n)
    """
    points = sorted(points)
    unique: list[Point] = []
    for point in points:
        if not unique or point != unique[-1]:
            unique.append(point)
    if len(unique) <= 1:
        return unique
    if keep_collinear and all(sgn(cross(point - unique[0], unique[-1] - unique[0])) == 0 for point in unique):
        return unique

    def bad_turn(a: Point, b: Point, c: Point) -> bool:
        turn = sgn(cross(b - a, c - b))
        return turn < 0 if keep_collinear else turn <= 0

    lower: list[Point] = []
    for point in unique:
        while len(lower) >= 2 and bad_turn(lower[-2], lower[-1], point):
            lower.pop()
        lower.append(point)
    upper: list[Point] = []
    for point in reversed(unique):
        while len(upper) >= 2 and bad_turn(upper[-2], upper[-1], point):
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def convex_polygon_diameter(points: list[Point]) -> tuple[int, int, float]:
    """Return one farthest pair on a convex polygon.

    Args:
        points: Convex polygon vertices in either cyclic orientation.
            Consecutive duplicate coordinates and a repeated closing vertex
            are allowed and ignored. Collinear inputs are supported.

    Returns:
        ``(i, j, squared_distance)`` for one farthest vertex pair, using
        indices into the original list. An all-equal input gives (0, 0, 0.0).
        Uses exact float comparisons rather than EPS for caliper rotation.

    Raises:
        ValueError: If the input is empty.

    Time Complexity:
        O(n)

    Space Complexity:
        O(n) for the vertex/index lists.
    """
    if not points:
        raise ValueError('points must not be empty')
    index = [0]
    for k in range(1, len(points)):
        if points[k].x != points[index[-1]].x or points[k].y != points[index[-1]].y:
            index.append(k)
    if len(index) > 1 and points[index[-1]].x == points[0].x and points[index[-1]].y == points[0].y:
        index.pop()
    points = [points[k] for k in index]
    n = len(points)
    if n == 1:
        return 0, 0, 0.0
    if n == 2:
        return index[0], index[1], Point.squared_distance(points[0], points[1])
    if polygon_signed_area(points) < 0.0:
        points = list(reversed(points))
        index = list(reversed(index))

    i = min(range(n), key=lambda k: (points[k].y, points[k].x))
    j = max(range(n), key=lambda k: (points[k].y, points[k].x))
    best_i, best_j = i, j
    best_dist = Point.squared_distance(points[i], points[j])
    steps_i = steps_j = 0
    # Bound each sweep independently: rounding on almost-collinear edges
    # need not bring the pair back to its exact starting state.
    while steps_i < n or steps_j < n:
        ni = (i + 1) % n
        nj = (j + 1) % n
        if steps_i == n or (steps_j < n and cross(points[ni] - points[i], points[nj] - points[j]) >= 0.0):
            j = nj
            steps_j += 1
        else:
            i = ni
            steps_i += 1
        dist = Point.squared_distance(points[i], points[j])
        if dist > best_dist:
            best_i, best_j, best_dist = i, j, dist
    return index[best_i], index[best_j], best_dist


def convex_cut(points: list[Point], line: LineLike) -> list[Point]:
    """Cut a convex polygon by a directed line.

    Args:
        points: Convex polygon vertices in cyclic order.
        line: Directed line. The returned polygon is the left side of this line.

    Returns:
        Vertices of the cut polygon in the input's cyclic orientation, or [].
        Boundary points are retained under EPS on cross products. Original
        retained vertices are shared; intersections are new Point objects.

    Raises:
        ValueError: If the line endpoints coincide, even for an empty polygon.

    Time Complexity:
        O(n)

    Space Complexity:
        O(n)
    """
    n = len(points)
    direction = line.direction()
    if direction.x == 0.0 and direction.y == 0.0:
        raise ValueError('line endpoints must be distinct')
    if n == 0:
        return []
    result: list[Point] = []
    for i in range(n):
        cur = points[i]
        nxt = points[(i + 1) % n]
        cur_side = sgn(cross(direction, cur - line.start))
        nxt_side = sgn(cross(direction, nxt - line.start))
        if cur_side >= 0:
            result.append(cur)
        if cur_side * nxt_side < 0:
            result.append(cross_point(Line(cur, nxt), line))
    return result


def closest_pair_distance(points: list[Point]) -> float:
    """Return the minimum Euclidean distance among point pairs.

    Args:
        points: At least two finite-coordinate points; the list is not reordered.

    Returns:
        Minimum distance between two different input indices. Duplicate
        coordinates give zero. Uses hypot to avoid unnecessary overflow or
        underflow from squaring distances.

    Raises:
        ValueError: If fewer than two points are given.

    Time Complexity:
        O(n log n), using bottom-up divide and conquer.

    Space Complexity:
        O(n)
    """
    n = len(points)
    if n < 2:
        raise ValueError('at least two points are required')
    coords = sorted((point.x, point.y) for point in points)
    best = float('inf')
    for i in range(1, n):
        distance = hypot(coords[i][0] - coords[i - 1][0], coords[i][1] - coords[i - 1][1])
        if distance < best:
            best = distance
    if best == 0.0:
        return 0.0

    ordered = coords[:]
    buffer = coords[:]
    width = 1
    while width < n:
        for left in range(0, n, 2 * width):
            mid = min(left + width, n)
            right = min(mid + width, n)
            if mid == right:
                buffer[left:right] = ordered[left:right]
                continue
            i, j, k = left, mid, left
            while i < mid and j < right:
                if ordered[i][1] <= ordered[j][1]:
                    buffer[k] = ordered[i]
                    i += 1
                else:
                    buffer[k] = ordered[j]
                    j += 1
                k += 1
            while i < mid:
                buffer[k] = ordered[i]
                i += 1
                k += 1
            while j < right:
                buffer[k] = ordered[j]
                j += 1
                k += 1

            split_x = coords[mid][0]
            strip = [buffer[k] for k in range(left, right) if -best < buffer[k][0] - split_x < best]
            for i in range(len(strip)):
                x, y = strip[i]
                for j in range(i + 1, min(i + 8, len(strip))):
                    dx = strip[j][0] - x
                    dy = strip[j][1] - y
                    if dy >= best:
                        break
                    distance = hypot(dx, dy)
                    if distance < best:
                        best = distance
        ordered, buffer = buffer, ordered
        width *= 2
    return best


def _circle_from_two_points(a: Point, b: Point) -> Circle:
    center = Point((a.x + b.x) * 0.5, (a.y + b.y) * 0.5)
    return Circle(center, distance_pp(center, a))


def _circle_from_three_points(a: Point, b: Point, c: Point) -> Circle:
    try:
        return triangle_circumcircle(a, b, c)
    except ValueError:
        pairs = ((a, b), (b, c), (c, a))
        p, q = max(pairs, key=lambda pair: Point.squared_distance(pair[0], pair[1]))
        return _circle_from_two_points(p, q)


def _circle_contains(circle: Circle, point: Point) -> bool:
    return sgn(distance_pp(circle.center, point) - circle.radius) <= 0


def minimum_enclosing_circle(points: list[Point]) -> Circle:
    """Return the minimum circle enclosing all points.

    Args:
        points: Non-empty list of finite-coordinate points. Duplicates are
            allowed. The input order is preserved.

    Returns:
        The minimum enclosing circle, up to floating-point rounding and EPS
        in containment/collinearity predicates.

    Raises:
        ValueError: If no point is given.

    Time Complexity:
        Expected O(n) over random shuffling; O(n**3) in the worst case.

    Space Complexity:
        O(n)
    """
    if not points:
        raise ValueError('at least one point is required')
    pts = points.copy()
    Random().shuffle(pts)
    circle = Circle(pts[0], 0.0)
    for i, p in enumerate(pts):
        if _circle_contains(circle, p):
            continue
        circle = Circle(p, 0.0)
        for j in range(i):
            q = pts[j]
            if _circle_contains(circle, q):
                continue
            circle = _circle_from_two_points(p, q)
            for k in range(j):
                r = pts[k]
                if not _circle_contains(circle, r):
                    circle = _circle_from_three_points(p, q, r)
    return circle


def circle_circle_intersection_area(circle1: Circle, circle2: Circle) -> float:
    """Return the area common to two circles.

    Args:
        circle1: First circle.
        circle2: Second circle.

    Returns:
        Non-negative disk intersection area. Zero-radius disks have area zero.
        Uses exact float comparisons for disjointness/containment rather than
        EPS, so small disks are not automatically assigned zero area.

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    r1 = circle1.radius
    r2 = circle2.radius
    if r1 == 0.0 or r2 == 0.0:
        return 0.0
    d = distance_pp(circle1.center, circle2.center)
    if d >= r1 + r2:
        return 0.0
    if d <= max(r1, r2) - min(r1, r2):
        r = min(r1, r2)
        return pi * r * r
    difference = (r1 - r2) * (r1 + r2)
    cos1 = (d * d + difference) / (2.0 * d * r1)
    cos2 = (d * d - difference) / (2.0 * d * r2)
    cos1 = max(-1.0, min(1.0, cos1))
    cos2 = max(-1.0, min(1.0, cos2))
    theta1 = 2.0 * acos(cos1)
    theta2 = 2.0 * acos(cos2)
    return 0.5 * r1 * r1 * (theta1 - sin(theta1)) + 0.5 * r2 * r2 * (theta2 - sin(theta2))


def _circle_sector_area(a: Point, b: Point, radius: float) -> float:
    return 0.5 * radius * radius * atan2(cross(a, b), dot(a, b))


def _circle_triangle_intersection_area(a: Point, b: Point, radius: float) -> float:
    direction = b - a
    acoef = norm2(direction)
    ts = [0.0, 1.0]
    if acoef != 0.0:
        signed_distance = cross(a, direction) / direction.abs()
        h2 = (radius - signed_distance) * (radius + signed_distance)
        if h2 > 0.0:
            midpoint = -dot(a, direction) / acoef
            half_chord = sqrt(h2 / acoef)
            t1 = midpoint - half_chord
            t2 = midpoint + half_chord
            if 0.0 < t1 < 1.0:
                ts.append(t1)
            if 0.0 < t2 < 1.0:
                ts.append(t2)
    ts.sort()
    area = 0.0
    for t1, t2 in zip(ts, ts[1:]):
        p = a + direction.scale(t1)
        q = a + direction.scale(t2)
        mid = a + direction.scale((t1 + t2) * 0.5)
        if mid.norm2() < radius * radius:
            area += cross(p, q) * 0.5
        else:
            area += _circle_sector_area(p, q, radius)
    return area


def circle_polygon_intersection_area(circle: Circle, polygon: list[Point]) -> float:
    """Return the area common to a circle and a simple polygon.

    Args:
        circle: Circle.
        polygon: Polygon vertices in cyclic order.

    Returns:
        Non-negative disk intersection area, independent of vertex orientation.
        Fewer than three vertices or a zero-radius circle gives zero.
        Uses exact float comparisons rather than EPS to preserve small areas.

    Time Complexity:
        O(n), where ``n = len(polygon)``.

    Space Complexity:
        O(1)
    """
    n = len(polygon)
    if n < 3 or circle.radius == 0.0:
        return 0.0
    area = 0.0
    center = circle.center
    radius = circle.radius
    for i in range(n):
        a = polygon[i] - center
        b = polygon[(i + 1) % n] - center
        area += _circle_triangle_intersection_area(a, b, radius)
    return area if area >= 0.0 else -area


def koch_curve_points(start: Point, end: Point, depth: int) -> list[Point]:
    """Return points on a Koch curve segment.

    Args:
        start: Start point.
        end: End point.
        depth: Number of replacement iterations.

    Returns:
        Points along the curve from ``start`` to ``end``, including both
        endpoints.

    Raises:
        ValueError: If ``depth`` is negative.

    Time Complexity:
        O(4^depth)

    Space Complexity:
        O(4^depth)
    """
    if depth < 0:
        raise ValueError('depth must be non-negative')
    points = [start, end]
    root3 = sqrt(3.0)
    for _ in range(depth):
        nxt = [points[0]]
        for a, b in zip(points, points[1:]):
            v = b - a
            s = a + v.scale(1.0 / 3.0)
            t = a + v.scale(2.0 / 3.0)
            w = t - s
            u = Point(s.x + (w.x - root3 * w.y) / 2.0, s.y + (root3 * w.x + w.y) / 2.0)
            nxt.extend((s, u, t, b))
        points = nxt
    return points


__all__ = [
    'EPS',
    'COUNTER_CLOCKWISE',
    'CLOCKWISE',
    'ONLINE_BACK',
    'ONLINE_FRONT',
    'ON_SEGMENT',
    'POINT_INSIDE_POLYGON',
    'POINT_ON_POLYGON',
    'POINT_OUTSIDE_POLYGON',
    'Line',
    'LineLike',
    'Point',
    'Segment',
    'Circle',
    'abs',
    'ccw',
    'circle_circle_cross_points',
    'circle_circle_intersection_area',
    'circle_line_cross_points',
    'circle_polygon_intersection_area',
    'circle_relation',
    'common_tangent_points',
    'cross',
    'cross_point',
    'closest_pair_distance',
    'convex_cut',
    'convex_hull',
    'convex_polygon_diameter',
    'distance',
    'distance_lp',
    'distance_pp',
    'distance_sp',
    'distance_ss',
    'dot',
    'equals',
    'get_eps',
    'intersect',
    'intersect_circle_line',
    'intersect_circle_segment',
    'is_orthogonal',
    'is_parallel',
    'is_convex_polygon',
    'koch_curve_points',
    'minimum_enclosing_circle',
    'norm2',
    'contains_point_in_polygon',
    'polygon_area',
    'polygon_signed_area',
    'projection',
    'reflection',
    'set_eps',
    'sgn',
    'tangent_points_from_point',
    'triangle_circumcircle',
    'triangle_incircle',
]
