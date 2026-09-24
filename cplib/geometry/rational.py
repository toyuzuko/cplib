#!/usr/bin/env python3

from __future__ import annotations

import random

from cplib.mathematics.rational import Rational
from cplib.algorithm.sort import merge_sort


class Point:
    """
    2D point with rational coordinates.

    Represents a point in 2D space using rational coordinates. Supports
    vector operations including addition, subtraction, dot product, and
    cross product. Coordinates must be finite. All operations maintain exact
    rational arithmetic. Do not mutate coordinates while a point is used as
    a dictionary key or set element.

    Complexity Notation:
        Bounds count rational arithmetic operations. Their cost depends on
        integer bit lengths and gcd normalization; it is not constant in the
        number of coordinate bits.

    Attributes:
        x (Rational): X-coordinate of the point.
        y (Rational): Y-coordinate of the point.

    Args:
        x: X-coordinate.
        y: Y-coordinate.

    Space Complexity:
        O(1)
    """
    def __init__(self, x: Rational | int, y: Rational | int):
        """
        Initialize a point with given coordinates.

        Args:
            x: X-coordinate (Rational or int).
            y: Y-coordinate (Rational or int).

        Returns:
            None.

        Time Complexity:
            O(1) besides the cost of rational construction.
        """
        self.x = x if isinstance(x, Rational) else Rational(x, 1)
        self.y = y if isinstance(y, Rational) else Rational(y, 1)

    def __add__(self, other: 'Point') -> 'Point':
        """Return the vector sum.

        Args:
            other: Point to add.

        Returns:
            A new point with componentwise sums.

        Time Complexity:
            O(1) rational operations.
        """
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point') -> 'Point':
        """Return the vector difference.

        Args:
            other: Point to subtract.

        Returns:
            A new point with componentwise differences.

        Time Complexity:
            O(1) rational operations.
        """
        return Point(self.x - other.x, self.y - other.y)

    def __neg__(self) -> 'Point':
        """Return a new point with both coordinates negated.

        Returns:
            The opposite vector.

        Time Complexity:
            O(1) rational operations.
        """
        return Point(-self.x, -self.y)

    def __eq__(self, other: object) -> bool:
        """Compare coordinates exactly.

        Args:
            other: Object to compare with.

        Returns:
            Whether coordinates are equal, or NotImplemented for other types.

        Time Complexity:
            O(1) rational comparisons.
        """
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __mul__(self, other: 'Point') -> Rational:
        """Compute the dot product.

        Args:
            other: Second vector.

        Returns:
            The exact dot product as a Rational.

        Time Complexity:
            O(1) rational operations.
        """
        return self.x * other.x + self.y * other.y

    def __matmul__(self, other: 'Point') -> Rational:
        """Compute the cross product.

        Args:
            other: Second vector.

        Returns:
            The exact cross product as a Rational.

        Time Complexity:
            O(1) rational operations.
        """
        return self.x * other.y - self.y * other.x

    def __lt__(self, other: 'Point') -> bool:
        if self.x != other.x:
            return self.x < other.x
        return self.y < other.y

    def sgn(self) -> int:
        """
        Get the sign/quadrant of the point for angular sorting.

        Returns:
            ``-1`` for points below the x-axis, ``0`` for the non-negative
            x-axis, and ``1`` otherwise.

        Time Complexity:
            O(1)
        """
        if self.y.sign() < 0: return -1
        if self.y.is_zero() and self.x.sign() >= 0: return 0
        return 1

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    @staticmethod
    def dot(p1: 'Point', p2: 'Point') -> Rational:
        """
        Compute dot product of two points (static method).

        Args:
            p1: Point value.
            p2: Point value.

        Returns:
            The exact dot product as a Rational.

        Time Complexity:
            O(1)
        """
        return p1.x * p2.x + p1.y * p2.y

    @staticmethod
    def cross(p1: 'Point', p2: 'Point') -> Rational:
        """
        Compute cross product of two points (static method).

        Args:
            p1: Point value.
            p2: Point value.

        Returns:
            The exact signed cross product as a Rational.

        Time Complexity:
            O(1)
        """
        return p1.x * p2.y - p1.y * p2.x

    @staticmethod
    def squared_distance(p1: 'Point', p2: 'Point') -> Rational:
        """
        Calculate squared distance between two points.

        Args:
            p1: Point value.
            p2: Point value.

        Returns:
            The exact squared Euclidean distance as a Rational.

        Time Complexity:
            O(1)
        """
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        return dx * dx + dy * dy


def argsort(points: list[Point]) -> list[Point]:
    """
    Sort points by angle around the origin.

    Angles increase counter-clockwise in (-pi, pi]: below the x-axis first,
    then the non-negative x-axis, then above the x-axis and the negative
    x-axis. The origin is assigned angle zero. Equal-angle points retain
    their input order; no distance tie-break is applied.

    Args:
        points: List of points to sort.

    Returns:
        A new list containing the original point objects, sorted by angle.
        The input list is not reordered.

    Time Complexity:
        O(n log n), where n is the number of points
    Space Complexity:
        O(n)
    """

    items = [(p.sgn(), p) for p in points]

    def cmp_func(item1: tuple[int, Point], item2: tuple[int, Point]) -> bool:
        s1, p1 = item1
        s2, p2 = item2
        if s1 != s2:
            return s1 < s2
        cross = Point.cross(p1, p2)
        return cross.sign() > 0

    return [p for _, p in merge_sort(items, cmp_func)]


def convex_hull(points: list[Point]) -> list[int]:
    """
    Compute the convex hull of a set of 2D points.

    Implements Andrew's monotone chain algorithm to find the convex hull.
    The algorithm constructs the hull in two parts: the lower hull from
    left to right, and the upper hull from right to left, then combines them.

    Args:
        points: List of Point objects representing points in 2D space.
                Can contain duplicate points.

    Returns:
        List of indices into the original points array representing the
        vertices of the convex hull in counter-clockwise order, starting
        from the leftmost point (and bottommost if there are ties). Collinear
        points between hull vertices are omitted. Duplicates use their first
        input index. Empty input returns []; a collinear set returns its two
        extreme points, or one point if all coordinates are equal.

    Time Complexity:
        O(n log n), where n is the number of points

    Space Complexity:
        O(n)
    """
    n = len(points)
    if n == 0: return []

    uniq_coords: list[Point] = []
    coord_to_idx: dict[Point, int] = {}

    for i, p in enumerate(points):
        if p not in coord_to_idx:
            coord_to_idx[p] = i
            uniq_coords.append(p)

    uniq_coords = merge_sort(uniq_coords, cmp = lambda p1, p2: p1.x < p2.x if p1.x != p2.x else p1.y < p2.y)

    if len(uniq_coords) <= 2: return [coord_to_idx[c] for c in uniq_coords]

    zero = Rational(0, 1)

    lower: list[Point] = []
    for coord in uniq_coords:
        while len(lower) >= 2 and Point.cross(lower[-1] - lower[-2], coord - lower[-2]) <= zero:
            lower.pop()
        lower.append(coord)

    upper: list[Point] = []
    for coord in reversed(uniq_coords):
        while len(upper) >= 2 and Point.cross(upper[-1] - upper[-2], coord - upper[-2]) <= zero:
            upper.pop()
        upper.append(coord)

    hull_coords = lower[:-1] + upper[:-1]
    hull_indices = [coord_to_idx[coord] for coord in hull_coords]

    return hull_indices


class Circle:
    """
    Circle with rational center coordinates and radius.

    Internally stores radius squared to maintain exact rational arithmetic.

    Attributes:
        center (Point): Center point of the circle.
        radius_squared (Rational): Square of the radius.

    Notes:
        The radius itself is not stored, so containment and algebraic
        comparisons remain exact without introducing square roots.

    Args:
        center: Circle center.
        radius: Circle radius.

    Raises:
        ValueError: If radius is negative.

    Space Complexity:
        O(1)
    """
    def __init__(self, center: Point, radius: Rational | int):
        """Initialize a circle with center and radius.

        Args:
            center: Center point of the circle.
            radius: Radius of the circle (non-negative).

        Returns:
            None.

        Raises:
            ValueError: If radius is negative.

        Time Complexity:
            O(1) rational operations.
        """
        if isinstance(radius, int):
            radius = Rational(radius, 1)
        if radius < Rational(0, 1):
            raise ValueError("Radius must be non-negative")
        self.center = center
        self.radius_squared = radius * radius

    @classmethod
    def from_squared_radius(cls, center: Point, radius_squared: Rational) -> 'Circle':
        """
        Create a circle from center and squared radius.

        Args:
            center: Center point of the circle.
            radius_squared: Square of the radius.

        Returns:
            Circle instance.

        Raises:
            ValueError: If radius_squared is negative.

        Time Complexity:
            O(1)
        """
        if radius_squared < Rational(0, 1):
            raise ValueError("Squared radius must be non-negative")
        circle = cls.__new__(cls)
        circle.center = center
        circle.radius_squared = radius_squared
        return circle

    def contains(self, point: Point) -> bool:
        """
        Check if a point is inside or on the circle.

        Args:
            point: The point to check.

        Returns:
            True if the point is inside or on the circle boundary.

        Time Complexity:
            O(1)
        """
        dx = point.x - self.center.x
        dy = point.y - self.center.y
        return dx * dx + dy * dy <= self.radius_squared

    def on_circle(self, point: Point) -> bool:
        """
        Check if a point is exactly on the circle boundary.

        Args:
            point: The point to check.

        Returns:
            True if the point is on the circle boundary.

        Time Complexity:
            O(1)
        """
        dx = point.x - self.center.x
        dy = point.y - self.center.y
        return dx * dx + dy * dy == self.radius_squared

    def __eq__(self, other: object) -> bool:
        """Check if two circles are equal."""
        if not isinstance(other, Circle):
            return NotImplemented
        return self.center == other.center and self.radius_squared == other.radius_squared

    def __repr__(self) -> str:
        return f"Circle(center={self.center}, radius_squared={self.radius_squared})"


def circumcircle(points: list[Point]) -> Circle:
    """
    Compute the circumcircle of 1-3 points.

    For three non-collinear points this is their unique circumcircle.
    For one point the radius is zero. For two points, or three collinear
    points, use the farthest pair as a diameter. In the collinear case,
    intermediate points are inside the circle, not on its boundary.

    Args:
        points: List of 1-3 Point objects.

    Returns:
        Circle object representing the circumcircle.

    Raises:
        ValueError: If no points or more than 3 points are provided.

    Notes:
        - For 1 point: Returns a circle centered at that point with radius 0
        - For 2 points: Returns the circle with those points as diameter
        - For 3 points: Returns the unique circle through all three
          (if collinear, uses the two furthest points as a diameter)

    Time Complexity:
        O(1)

    Space Complexity:
        O(1)
    """
    n = len(points)

    if n == 0: raise ValueError("At least one point is required to define a circumcircle")
    if n == 1: return Circle.from_squared_radius(points[0], Rational(0, 1))
    if n == 2:
        p1, p2 = points
        cx = (p1.x + p2.x) / Rational(2, 1)
        cy = (p1.y + p2.y) / Rational(2, 1)
        center = Point(cx, cy)
        r_sq = Point.squared_distance(p1, center)
        return Circle.from_squared_radius(center, r_sq)
    if n > 3: raise ValueError("Circumcircle is defined for at most 3 points")

    p1, p2, p3 = points
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y

    det = Rational(2, 1) * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))

    if det.is_zero():
        pairs = [(p1, p2), (p1, p3), (p2, p3)]
        far_p1, far_p2 = max(pairs, key=lambda pr: Point.squared_distance(pr[0], pr[1]))
        return circumcircle([far_p1, far_p2])

    x1_sq_y1_sq = x1 * x1 + y1 * y1
    x2_sq_y2_sq = x2 * x2 + y2 * y2
    x3_sq_y3_sq = x3 * x3 + y3 * y3
    cx = (x1_sq_y1_sq * (y2 - y3) + x2_sq_y2_sq * (y3 - y1) + x3_sq_y3_sq * (y1 - y2)) / det
    cy = (x1_sq_y1_sq * (x3 - x2) + x2_sq_y2_sq * (x1 - x3) + x3_sq_y3_sq * (x2 - x1)) / det
    center = Point(cx, cy)
    r_sq = Point.squared_distance(p1, center)
    return Circle.from_squared_radius(center, r_sq)


def minimum_enclosing_circle(points: list[Point]) -> Circle:
    """
    Find the minimum enclosing circle of a set of 2D points.

    Uses Welzl's randomized algorithm to find the smallest circle that
    contains all given points.

    Args:
        points: Finite-coordinate points. Duplicates are allowed, and the
            input list is not reordered.

    Returns:
        Circle object representing the minimum enclosing circle.

    Notes:
        - Returns circle with center at origin and radius 0 for empty input
        - The algorithm is randomized but always finds the unique minimum circle
        - The Circle internally stores radius_squared to maintain exact arithmetic

    Time Complexity:
        Expected O(n) rational operations, where n is the number of points

    Space Complexity:
        O(n)
    """
    n = len(points)
    if n == 0:
        return Circle.from_squared_radius(Point(Rational(0, 1), Rational(0, 1)), Rational(0, 1))

    random.shuffle(indices := list(range(n)))

    boundary_points: list[int] = []

    stack = [(len(indices), len(boundary_points), -1)]
    result_stack: list[Circle] = []

    while stack:
        idx_len, bound_len, p_idx = stack.pop()

        if p_idx >= 0:
            # bound_len matches current boundary size: RETURN_FIRST
            if bound_len == len(boundary_points):
                c = result_stack.pop()
                if c.contains(points[p_idx]):
                    result_stack.append(c)
                    indices.append(p_idx)
                else:
                    boundary_points.append(p_idx)
                    stack.append((idx_len, bound_len, p_idx))  # Will be RETURN_SECOND
                    stack.append((idx_len, bound_len + 1, -1))  # New CALL
                continue
            # bound_len < current boundary size: RETURN_SECOND
            else:
                boundary_points.pop()
                indices.append(p_idx)
                continue

        # p_idx == -1: CALL
        if bound_len == 3:
            result_stack.append(circumcircle([points[boundary_points[i]] for i in range(3)]))
            continue

        if idx_len == 0:
            if bound_len == 0:
                result_stack.append(Circle.from_squared_radius(Point(Rational(0, 1), Rational(0, 1)), Rational(0, 1)))
            elif bound_len == 1:
                result_stack.append(Circle.from_squared_radius(points[boundary_points[0]], Rational(0, 1)))
            elif bound_len == 2:
                result_stack.append(circumcircle([points[boundary_points[i]] for i in range(2)]))
            continue

        p = indices.pop()
        stack.append((idx_len - 1, bound_len, p))  # RETURN_FIRST
        stack.append((idx_len - 1, bound_len, -1))  # CALL

    return result_stack[0] if result_stack else Circle.from_squared_radius(Point(Rational(0, 1), Rational(0, 1)), Rational(0, 1))


class Segment:
    """
    Directed line segment on rational coordinates.

    Attributes:
        start: First endpoint.
        end: Second endpoint.
        dir: Direction vector ``end - start``.
        slope: Formal slope ``dir.y / dir.x``.

    Notes:
        Endpoints must be distinct and finite. A vertical segment has slope
        +infinity when directed upward and -infinity when directed downward.
        The direction and slope are computed once; do not mutate endpoints
        afterward.

    Args:
        start: Point value.
        end: Point value.

    Raises:
        ValueError: If the endpoints coincide (the slope would be 0/0).

    Space Complexity:
        O(1)
    """

    def __init__(self, start: Point, end: Point):
        """
        Initialize a directed segment from ``start`` to ``end``.

        Args:
            start: First endpoint.
            end: Second endpoint.

        Returns:
            None.

        Raises:
            ValueError: If the endpoints coincide.

        Time Complexity:
            O(1) besides the cost of rational arithmetic.
        """
        self.start = start
        self.end = end
        self.dir = end - start
        self.slope = self.dir.y / self.dir.x
