#!/usr/bin/env python3

from __future__ import annotations

import random
from bisect import bisect_left, bisect_right
from math import gcd, isqrt

from cplib.algorithm.sort import merge_sort
from cplib.datastructure.dsu import DisjointSetUnion
from cplib.datastructure.fenwicktree import FenwickTree


class Point:
    """
    2D point with integer coordinates.

    Do not mutate coordinates while a point is used as a dictionary key or
    set element. Complexity bounds count arithmetic operations and do not
    include the cost of arbitrary-precision integer arithmetic.

    Attributes:
        x (int): X-coordinate of the point.
        y (int): Y-coordinate of the point.

    Space Complexity:
        O(1)

    Examples:
        >>> p1 = Point(3, 4)
        >>> p2 = Point(1, 2)
        >>> p3 = p1 + p2  # Point(4, 6)
        >>> dot = p1 * p2  # 3*1 + 4*2 = 11
        >>> cross = p1 @ p2  # 3*2 - 4*1 = 2
    """
    def __init__(self, x: int, y: int):
        """Initialize a point with given coordinates.

        Args:
            x: X-coordinate.
            y: Y-coordinate.

        Returns:
            None.

        Time Complexity:
            O(1)

        Examples:
            >>> p = Point(3, 4)
            >>> (p.x, p.y)
            (3, 4)
        """
        self.x = x
        self.y = y

    def __add__(self, other: 'Point') -> 'Point':
        """Add two points (vector addition).

        Args:
            other: The point to add.

        Returns:
            A new Point representing the sum of the two points.
        """
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point') -> 'Point':
        """Subtract two points (vector subtraction).

        Args:
            other: The point to subtract.

        Returns:
            A new Point representing the difference of the two points.
        """
        return Point(self.x - other.x, self.y - other.y)

    def __neg__(self) -> 'Point':
        """Negate a point (reverse direction).

        Returns:
            A new Point with negated coordinates.
        """
        return Point(-self.x, -self.y)

    def __eq__(self, other: object) -> bool:
        """Check if two points are equal.

        Args:
            other: The object to compare with.

        Returns:
            True if other is a Point with equal x and y coordinates, False otherwise.
        """
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __mul__(self, other: 'Point') -> int:
        """Compute dot product of two points.

        Args:
            other: The point to compute dot product with.

        Returns:
            The dot product (scalar value).
        """
        return self.x * other.x + self.y * other.y

    def __matmul__(self, other: 'Point') -> int:
        """Compute cross product of two points.

        The cross product in 2D gives the signed area of the parallelogram
        formed by the two vectors.

        Args:
            other: The point to compute cross product with.

        Returns:
            The cross product (scalar value). Positive if other is counter-clockwise
            from self, negative if clockwise, zero if collinear.
        """
        return self.x * other.y - self.y * other.x

    def __lt__(self, other: 'Point') -> bool:
        if self.x != other.x:
            return self.x < other.x
        return self.y < other.y

    def sgn(self) -> int:
        """
        Get the sign/quadrant of the point for angular sorting.

        Used for sorting points by angle. Points are classified into three groups:
        -1: Below x-axis (y < 0)
         0: On positive x-axis (y = 0, x >= 0)
         1: Above x-axis or on negative x-axis (y > 0 or (y = 0, x < 0))

        Returns:
            -1, 0, or 1 based on the point's position relative to x-axis.

        Time Complexity:
            O(1)

        Examples:
            >>> Point(2, 0).sgn()
            0
        """
        if self.y < 0: return -1
        if self.y == 0 and self.x >= 0: return 0
        return 1

    def __hash__(self) -> int:
        u = self.x * 2 if self.x >= 0 else -self.x * 2 - 1
        v = self.y * 2 if self.y >= 0 else -self.y * 2 - 1
        s = u + v
        return (s * (s + 1) // 2) + v

    @staticmethod
    def dot(p1: 'Point', p2: 'Point') -> int:
        """
        Compute dot product of two points (static method).

        Args:
            p1: First point.
            p2: Second point.

        Returns:
            The dot product of p1 and p2.

        Time Complexity:
            O(1)

        Examples:
            >>> Point.dot(Point(1, 2), Point(3, 4))
            11
        """
        return p1.x * p2.x + p1.y * p2.y

    @staticmethod
    def cross(p1: 'Point', p2: 'Point') -> int:
        """
        Compute cross product of two points (static method).

        Args:
            p1: First point.
            p2: Second point.

        Returns:
            The cross product of p1 and p2.

        Time Complexity:
            O(1)

        Examples:
            >>> Point.cross(Point(1, 0), Point(0, 1))
            1
        """
        return p1.x * p2.y - p1.y * p2.x

    @staticmethod
    def squared_distance(p1: 'Point', p2: 'Point') -> int:
        """
        Calculate squared distance between two points.

        Args:
            p1: First point.
            p2: Second point.

        Returns:
            Squared distance between the points.

        Time Complexity:
            O(1)

        Examples:
            >>> Point.squared_distance(Point(0, 0), Point(3, 4))
            25
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

    Examples:
        >>> ordered = argsort([Point(0, 1), Point(1, 0), Point(-1, 0)])
        >>> [(p.x, p.y) for p in ordered]
        [(1, 0), (0, 1), (-1, 0)]
    """
    items = [(p.sgn(), p) for p in points]

    def cmp_func(item1: tuple[int, Point], item2: tuple[int, Point]) -> bool:
        s1, p1 = item1
        s2, p2 = item2
        if s1 != s2:
            return s1 < s2
        return Point.cross(p1, p2) > 0

    return [p for _, p in merge_sort(items, cmp_func)]


def closest_points(points: list[Point]) -> tuple[int, int]:
    """
    Find the pair of points with minimum Euclidean distance.

    Implements an efficient divide-and-conquer algorithm to find the closest
    pair of points in a 2D plane. The algorithm builds a segment tree-like
    structure bottom-up, maintaining y-sorted arrays for each segment and
    computing closest pairs iteratively from pairs of child intervals.

    Args:
        points: List of Point objects representing points in 2D space.
                Must contain at least 2 points.

    Returns:
        Tuple of two indices (i, j) representing the closest pair of points,
        where points[i] and points[j] have the minimum distance among all pairs.

    Raises:
        ValueError: If fewer than 2 points are provided.

    Time Complexity:
        O(n log n), where n is the number of points

    Space Complexity:
        O(n log n)

    Examples:
        >>> pts = [Point(0, 0), Point(5, 5), Point(1, 1)]
        >>> closest_points(pts)
        (0, 2)
    """
    n = len(points)
    if n < 2: raise ValueError("at least two points required")

    order_x = merge_sort(list(range(n)), cmp = lambda i, j: points[i].x < points[j].x)

    xs = [points[i].x for i in order_x]
    ys = [points[i].y for i in order_x]
    inf = (max(xs) - min(xs))**2 + (max(ys) - min(ys))**2 + 1
    log  = (n - 1).bit_length()
    size = 1 << log
    node_y:  list[list[int]] = [[] for _ in range(2 * size)]
    node_d:  list[int] = [inf] * (2 * size)
    node_pr: list[tuple[int, int]] = [(-1, -1)] * (2 * size)

    for v in range(size, size + n):
        idx = v - size
        node_y[v] = [idx]

    best_d = inf
    best_pair = (-1, -1)

    for v in range(size - 1, 0, -1):
        lc, rc = v * 2, v * 2 + 1
        if not node_y[lc]:
            node_y[v], node_d[v], node_pr[v] = node_y[rc], node_d[rc], node_pr[rc]
            continue
        if not node_y[rc]:
            node_y[v], node_d[v], node_pr[v] = node_y[lc], node_d[lc], node_pr[lc]
            continue
        dl, dr = node_d[lc], node_d[rc]
        d, pair = (dl, node_pr[lc]) if dl < dr else (dr, node_pr[rc])

        merged: list[int] = []
        ly, ry = node_y[lc], node_y[rc]
        i = j = 0
        while i < len(ly) and j < len(ry): # merge sort
            if ys[ly[i]] <= ys[ry[j]]:
                merged.append(ly[i])
                i += 1
            else:
                merged.append(ry[j])
                j += 1
        merged.extend(ly[i:])
        merged.extend(ry[j:])

        if d == inf:
            i0, i1 = ly[0], ry[0]
            dx = xs[i0] - xs[i1]
            dy = ys[i0] - ys[i1]
            d = dx * dx + dy * dy
            pair = (order_x[i0], order_x[i1])

        depth   = v.bit_length() - 1
        seg_len = 1 << (log - depth)
        start   = (v << (log - depth)) - size
        mid_x = xs[start + (seg_len >> 1)]
        strip = [idx for idx in merged if (xs[idx] - mid_x) ** 2 < d]

        for s in range(len(strip)):
            y0, x0, i0 = ys[strip[s]], xs[strip[s]], order_x[strip[s]]
            for t in range(s + 1, min(s + 8, len(strip))):
                dy = ys[strip[t]] - y0
                if dy * dy >= d:
                    break
                dx = xs[strip[t]] - x0
                dsq = dx * dx + dy * dy
                if dsq < d:
                    d = dsq
                    pair = (i0, order_x[strip[t]])

        node_y[v], node_d[v], node_pr[v] = merged, d, pair
        if d < best_d:
            best_d, best_pair = d, pair

    return best_pair


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

    Examples:
        >>> points = [Point(0, 0), Point(2, 0), Point(2, 2), Point(0, 2), Point(1, 1)]
        >>> hull_indices = convex_hull(points)
        >>> # hull_indices contains indices [0, 1, 2, 3] (the square's vertices)

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

    lower: list[Point] = []
    for coord in uniq_coords:
        while len(lower) >= 2 and Point.cross(lower[-1] - lower[-2], coord - lower[-2]) <= 0:
            lower.pop()
        lower.append(coord)

    upper: list[Point] = []
    for coord in reversed(uniq_coords):
        while len(upper) >= 2 and Point.cross(upper[-1] - upper[-2], coord - upper[-2]) <= 0:
            upper.pop()
        upper.append(coord)

    hull_coords = lower[:-1] + upper[:-1]
    hull_indices = [coord_to_idx[coord] for coord in hull_coords]

    return hull_indices


class _DecrementalLeftHull:
    def __init__(self, coords: list[tuple[int, int]]) -> None:
        self.xs = [x for x, _ in coords]
        self.ys = [y for _, y in coords]
        self.n = len(coords)
        size = max(1, 2 * self.n)
        self.bl = [0] * size
        self.br = [0] * size
        self.left = [0] * size
        self.right = [0] * size
        self.lch = [-1] * size
        self.rch = [-1] * size
        self.root = 0 if self.n else -1
        if self.n:
            self._build(0, 0, self.n)

    def _cross(self, a: int, b: int, c: int) -> int:
        return (self.xs[b] - self.xs[a]) * (self.ys[c] - self.ys[a]) - (self.ys[b] - self.ys[a]) * (self.xs[c] - self.xs[a])

    def _is_leaf(self, node: int) -> bool:
        return self.lch[node] == -1 and self.rch[node] == -1

    def _pull(self, node: int) -> None:
        lnode = self.lch[node]
        rnode = self.rch[node]
        split_y = self.ys[self.left[rnode]]
        while not self._is_leaf(lnode) or not self._is_leaf(rnode):
            a = self.bl[lnode]
            b = self.br[lnode]
            c = self.bl[rnode]
            d = self.br[rnode]
            if a != b and self._cross(a, b, c) > 0:
                lnode = self.lch[lnode]
            elif c != d and self._cross(b, c, d) > 0:
                rnode = self.rch[rnode]
            elif a == b:
                rnode = self.lch[rnode]
            elif c == d:
                lnode = self.rch[lnode]
            else:
                s1 = self._cross(a, b, c)
                s2 = self._cross(b, a, d)
                if s1 + s2 == 0 or s1 * self.ys[d] + s2 * self.ys[c] < split_y * (s1 + s2):
                    lnode = self.rch[lnode]
                else:
                    rnode = self.lch[rnode]
        self.bl[node] = self.left[lnode]
        self.br[node] = self.left[rnode]

    def _build(self, node: int, left: int, right: int) -> None:
        self.left[node] = left
        self.right[node] = right
        if right - left == 1:
            self.lch[node] = -1
            self.rch[node] = -1
            self.bl[node] = left
            self.br[node] = left
            return
        mid = (left + right) >> 1
        self.lch[node] = node + 1
        self.rch[node] = node + 2 * (mid - left)
        self._build(self.lch[node], left, mid)
        self._build(self.rch[node], mid, right)
        self._pull(node)

    def _erase(self, node: int, left: int, right: int) -> int:
        if node == -1 or right <= self.left[node] or self.right[node] <= left:
            return node
        if left <= self.left[node] and self.right[node] <= right:
            return -1
        self.lch[node] = self._erase(self.lch[node], left, right)
        self.rch[node] = self._erase(self.rch[node], left, right)
        if self.lch[node] == -1:
            return self.rch[node]
        if self.rch[node] == -1:
            return self.lch[node]
        self._pull(node)
        return node

    def _collect_hull(self, node: int, left: int, right: int, res: list[int]) -> None:
        if self._is_leaf(node):
            res.append(self.left[node])
            return
        if right <= self.bl[node]:
            self._collect_hull(self.lch[node], left, right, res)
        elif self.br[node] <= left:
            self._collect_hull(self.rch[node], left, right, res)
        else:
            self._collect_hull(self.lch[node], left, self.bl[node], res)
            self._collect_hull(self.rch[node], self.br[node], right, res)

    def get_hull(self) -> list[int]:
        if self.root == -1:
            return []
        res: list[int] = []
        self._collect_hull(self.root, 0, self.n - 1, res)
        return res

    def erase(self, index: int) -> None:
        self.root = self._erase(self.root, index, index + 1)


def convex_layers(points: list[Point]) -> list[int]:
    """
    Compute onion-decomposition layers of distinct integer points.

    Repeatedly remove every point on the boundary of the convex hull of the
    remaining points. The returned layer numbers are 1-indexed.

    Args:
        points: Distinct points.

    Returns:
        ``layers[i]`` is the iteration in which ``points[i]`` is removed.

    Raises:
        ValueError: If duplicate points are given.

    Time Complexity:
        ``O(n log^2 n)``

    Space Complexity:
        ``O(n)``
    """
    n = len(points)
    if n == 0:
        return []
    sorted_points = sorted((p.y, p.x, i) for i, p in enumerate(points))
    for i in range(1, n):
        if sorted_points[i][:2] == sorted_points[i - 1][:2]:
            raise ValueError('points must be distinct')

    coords = [(x, y) for y, x, _ in sorted_points]
    original_index = [idx for _, _, idx in sorted_points]
    left = _DecrementalLeftHull(coords)
    right_coords = [(-x, -y) for x, y in reversed(coords)]
    right = _DecrementalLeftHull(right_coords)
    layers_in_sorted_order = [0] * n
    answer = [0] * n

    removed_count = 0
    layer = 1
    while removed_count < n:
        hull = set(left.get_hull())
        for idx in right.get_hull():
            hull.add(n - 1 - idx)
        for idx in hull:
            layers_in_sorted_order[idx] = layer
            removed_count += 1
            left.erase(idx)
            right.erase(n - 1 - idx)
        layer += 1

    for sorted_idx, layer in enumerate(layers_in_sorted_order):
        answer[original_index[sorted_idx]] = layer
    return answer


def furthest_points(points: list[Point]) -> tuple[int, int]:
    """
    Find the pair of points with maximum Euclidean distance.

    Implements the rotating calipers algorithm on the convex hull to find
    the diameter (furthest pair) of a point set. The algorithm exploits the
    property that the furthest pair must lie on the convex hull.

    Args:
        points: List of Point objects representing points in 2D space.
                Must contain at least 2 points.

    Returns:
        Tuple of two indices (i, j) representing the furthest pair of points,
        where points[i] and points[j] have the maximum distance among all pairs.

    Raises:
        ValueError: If fewer than 2 points are provided.

    Examples:
        >>> points = [Point(0, 0), Point(3, 0), Point(0, 4)]
        >>> i, j = furthest_points(points)
        >>> # Returns indices of points (3, 0) and (0, 4)
        >>> # which have distance 5 (by Pythagorean theorem: sqrt(3^2 + 4^2) = 5)

    Time Complexity:
        O(n log n), where n is the number of points

    Space Complexity:
        O(n)
    """
    n = len(points)
    if n < 2: raise ValueError("at least two points required")

    hull = convex_hull(points)
    m = len(hull)
    if m < 2: return 0, 1
    ch_points = [points[i] for i in hull]

    j = 1
    best_d = 0
    best_pair = (hull[0], hull[1])

    for i in range(m):
        ni = (i + 1) % m
        while True:
            nj = (j + 1) % m
            area_now = Point.cross(ch_points[ni] - ch_points[i], ch_points[j] - ch_points[i])
            area_next = Point.cross(ch_points[ni] - ch_points[i], ch_points[nj] - ch_points[i])
            if area_next > area_now:
                j = nj
            else:
                break
        d = Point.squared_distance(ch_points[i], ch_points[j])
        if d > best_d:
            best_d = d
            best_pair = (hull[i], hull[j])
        d = Point.squared_distance(ch_points[ni], ch_points[j])
        if d > best_d:
            best_d = d
            best_pair = (hull[ni], hull[j])

    return best_pair


def minimum_enclosing_circle(points: list[Point]) -> list[bool]:
    """
    Return which points lie on the minimum enclosing circle boundary.

    The implementation is an iterative form of Welzl's randomized algorithm.
    Instead of returning the circle itself, it marks the input points that lie
    on the boundary of the unique minimum enclosing circle.

    Args:
        points: Input points.

    Returns:
        list[bool]: Boundary flags in the same order as ``points``.

    Time Complexity:
        Expected O(n), where n is the number of points

    Space Complexity:
        O(n)

    Examples:
        >>> minimum_enclosing_circle([Point(0, 0), Point(2, 0), Point(1, 1)])
        [True, True, True]
    """
    n = len(points)
    if n == 0:
        return [False] * n

    order = list(range(n))
    random.shuffle(order)

    def _make_circle(boundary_indices: list[int]) -> tuple[int, int, int, int]:
        if len(boundary_indices) == 0:
            return (0, 0, 1, -1)

        if len(boundary_indices) == 1:
            i = boundary_indices[0]
            return (points[i].x, points[i].y, 1, 0)

        if len(boundary_indices) == 2:
            i, j = boundary_indices
            xi, yi = points[i].x, points[i].y
            xj, yj = points[j].x, points[j].y
            cx_num = xi + xj
            cy_num = yi + yj
            den = 2
            dx = xi * den - cx_num
            dy = yi * den - cy_num
            r_sq_num = dx * dx + dy * dy
            return (cx_num, cy_num, den, r_sq_num)

        i, j, k = boundary_indices
        x1, y1 = points[i].x, points[i].y
        x2, y2 = points[j].x, points[j].y
        x3, y3 = points[k].x, points[k].y

        det = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))

        if det == 0:
            pairs = [(i, j), (i, k), (j, k)]
            far_i, far_j = max(pairs, key=lambda pr: Point.squared_distance(points[pr[0]], points[pr[1]]))
            return _make_circle([far_i, far_j])

        ux_num = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2))
        uy_num = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1))

        den = det if det > 0 else -det
        if det < 0:
            ux_num, uy_num = -ux_num, -uy_num

        dx = x1 * den - ux_num
        dy = y1 * den - uy_num
        r_sq_num = dx * dx + dy * dy
        return (ux_num, uy_num, den, r_sq_num)

    def _contains(circ: tuple[int, int, int, int], idx: int) -> bool:
        cx_num, cy_num, den, r_sq_num = circ
        dx = points[idx].x * den - cx_num
        dy = points[idx].y * den - cy_num
        return dx * dx + dy * dy <= r_sq_num

    indices = order[:]
    boundary_points: list[int] = []

    stack = [(len(indices), len(boundary_points), -1)]
    result_stack: list[tuple[int, int, int, int]] = []

    while stack:
        idx_len, bound_len, p_idx = stack.pop()

        if p_idx >= 0:
            # bound_len matches current boundary size: RETURN_FIRST
            if bound_len == len(boundary_points):
                c = result_stack.pop()
                if _contains(c, p_idx):
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
            result_stack.append(_make_circle([boundary_points[i] for i in range(3)]))
            continue

        if idx_len == 0:
            if bound_len == 0:
                result_stack.append((0, 0, 1, -1))
            elif bound_len == 1:
                i = boundary_points[0]
                result_stack.append((points[i].x, points[i].y, 1, 0))
            elif bound_len == 2:
                result_stack.append(_make_circle([boundary_points[i] for i in range(2)]))
            continue

        p = indices.pop()
        stack.append((idx_len - 1, bound_len, p))  # RETURN_FIRST
        stack.append((idx_len - 1, bound_len, -1))  # CALL

    cx_num, cy_num, den, r_sq_num = result_stack[0] if result_stack else (0, 0, 1, -1)

    def _on_circle(idx: int) -> bool:
        dx = points[idx].x * den - cx_num
        dy = points[idx].y * den - cy_num
        return dx * dx + dy * dy == r_sq_num

    return [_on_circle(i) for i in range(n)]


class Segment:
    """
    Line segment defined by two endpoints.

    Attributes:
        start (Point): Starting point of the segment.
        end (Point): Ending point of the segment.

    Space Complexity:
        O(1)

    Examples:
        >>> s1 = Segment(Point(0, 0), Point(2, 2))
        >>> s2 = Segment(Point(0, 2), Point(2, 0))
        >>> s1.intersects(s2)  # True, they intersect at (1, 1)
        True
    """
    def __init__(self, start: Point, end: Point):
        """Initialize a segment with two endpoints.

        Args:
            start: Starting point of the segment.
            end: Ending point of the segment.

        Returns:
            None.

        Time Complexity:
            O(1)

        Examples:
            >>> s = Segment(Point(0, 0), Point(1, 1))
            >>> ((s.start.x, s.start.y), (s.end.x, s.end.y))
            ((0, 0), (1, 1))
        """
        self.start = start
        self.end = end

    def __eq__(self, other: object) -> bool:
        """Check if two segments are equal.

        Two segments are equal if they have the same endpoints (in any order).

        Args:
            other: The object to compare with.

        Returns:
            True if other is a Segment with the same endpoints, False otherwise.
        """
        if not isinstance(other, Segment):
            return NotImplemented
        return (self.start == other.start and self.end == other.end) or (self.start == other.end and self.end == other.start)

    def length(self) -> float:
        """
        Calculate the Euclidean length of the segment.

        Returns:
            The length of the segment as a float.

        Time Complexity:
            O(1)

        Examples:
            >>> Segment(Point(0, 0), Point(3, 4)).length()
            5.0
        """
        return Point.squared_distance(self.start, self.end)**0.5

    def contains(self, point: Point) -> bool:
        """
        Check if a point lies on the segment.

        Args:
            point: The point to check.

        Returns:
            True if the point lies on the segment, False otherwise.

        Time Complexity:
            O(1)

        Examples:
            >>> Segment(Point(0, 0), Point(2, 2)).contains(Point(1, 1))
            True
        """
        return Point.cross(point - self.start, self.end - self.start) == 0 and \
               min(self.start.x, self.end.x) <= point.x <= max(self.start.x, self.end.x) and \
               min(self.start.y, self.end.y) <= point.y <= max(self.start.y, self.end.y)

    def intersects(self, other: 'Segment') -> bool:
        """
        Check if two segments intersect.

        Args:
            other: The segment to check intersection with.

        Returns:
            True if the segments intersect (including endpoint touching), False otherwise.

        Time Complexity:
            O(1)

        Examples:
            >>> s1 = Segment(Point(0, 0), Point(2, 2))
            >>> s2 = Segment(Point(0, 2), Point(2, 0))
            >>> s1.intersects(s2)
            True
        """
        d1 = Point.cross(other.end - other.start, self.start - other.start)
        d2 = Point.cross(other.end - other.start, self.end - other.start)
        d3 = Point.cross(self.end - self.start, other.start - self.start)
        d4 = Point.cross(self.end - self.start, other.end - self.start)

        if d1 * d2 < 0 and d3 * d4 < 0:
            return True
        if d1 == 0 and other.contains(self.start):
            return True
        if d2 == 0 and other.contains(self.end):
            return True
        if d3 == 0 and self.contains(other.start):
            return True
        if d4 == 0 and self.contains(other.end):
            return True
        return False


def count_manhattan_intersections(segments: list[Segment]) -> int:
    """Count intersections between horizontal and vertical line segments.

    Args:
        segments: Axis-aligned line segments. A zero-length segment is
            classified as horizontal.

    Returns:
        Number of intersecting horizontal-vertical pairs, including endpoint
        touching. Multiple pairs at the same coordinate are counted separately.
        Pairs of two horizontal or two vertical segments are not counted.

    Raises:
        ValueError: If a segment is neither horizontal nor vertical.

    Time Complexity:
        O(n log n), where n is the number of segments.

    Space Complexity:
        O(n)
    """
    horizontal: list[tuple[int, int, int]] = []
    vertical: list[tuple[int, int, int]] = []
    for segment in segments:
        x1 = segment.start.x
        y1 = segment.start.y
        x2 = segment.end.x
        y2 = segment.end.y
        if y1 == y2:
            if x1 > x2:
                x1, x2 = x2, x1
            horizontal.append((x1, x2, y1))
        elif x1 == x2:
            if y1 > y2:
                y1, y2 = y2, y1
            vertical.append((x1, y1, y2))
        else:
            raise ValueError('all segments must be axis-aligned')

    if not horizontal or not vertical:
        return 0

    ys = sorted({y for _, _, y in horizontal})
    bit = FenwickTree(len(ys))
    events: list[tuple[int, int, int, int]] = []
    for x1, x2, y in horizontal:
        yi = bisect_left(ys, y)
        events.append((x1, 0, yi, yi))
        events.append((x2, 2, yi, yi))
    for x, y1, y2 in vertical:
        events.append((x, 1, y1, y2))

    answer = 0
    for _, kind, y1, y2 in sorted(events):
        if kind == 0:
            bit.add(y1, 1)
        elif kind == 2:
            bit.add(y1, -1)
        else:
            left = bisect_left(ys, y1)
            right = bisect_right(ys, y2)
            answer += bit.range_sum(left, right)
    return answer


class Circle:
    """
    Circle represented exactly with scaled integer center coordinates.

    The actual center is
    ``(center_num.x / denominator, center_num.y / denominator)`` and the
    squared radius is ``radius_squared_num / denominator^2``. Integer-centered
    circles constructed by ``Circle(center, radius)`` keep the same public
    ``center`` and ``radius`` access as before.

    Attributes:
        center_num: Scaled numerator of the center coordinates.
        denominator: Positive center denominator.
        radius_squared_num: Numerator of the squared radius under the same
            denominator scale.

    Space Complexity:
        O(1)

    Examples:
        >>> c1 = Circle(Point(0, 0), 5)
        >>> c2 = Circle.from_diameter(Point(0, 0), Point(2, 0))
        >>> c1.contains(Point(3, 4))  # True
        True
        >>> c1.intersects(c2)  # True
        True
    """

    def __init__(self, center: Point, radius: int):
        """Initialize a circle with center and radius.

        Args:
            center: Center point of the circle.
            radius: Radius of the circle (non-negative integer).

        Returns:
            None.

        Time Complexity:
            O(1)

        Examples:
            >>> c = Circle(Point(0, 0), 5)
            >>> ((c.center.x, c.center.y), c.radius)
            ((0, 0), 5)
        """
        if radius < 0:
            raise ValueError('radius must be non-negative')
        self.center_num = Point(center.x, center.y)
        self.denominator = 1
        self.radius_squared_num = radius * radius

    @classmethod
    def _from_scaled(cls, center_x_num: int, center_y_num: int, denominator: int, radius_squared_num: int) -> 'Circle':
        assert denominator > 0  # positive scale denominator
        assert radius_squared_num >= 0  # squared radius numerator
        g = gcd(gcd(abs(center_x_num), abs(center_y_num)), denominator)
        if g > 1:
            center_x_num //= g
            center_y_num //= g
            denominator //= g
            radius_squared_num //= g * g
        circle = cls.__new__(cls)
        circle.center_num = Point(center_x_num, center_y_num)
        circle.denominator = denominator
        circle.radius_squared_num = radius_squared_num
        return circle

    @classmethod
    def from_diameter(cls, p1: Point, p2: Point) -> 'Circle':
        """
        Construct the circle whose diameter endpoints are ``p1`` and ``p2``.

        Args:
            p1: First diameter endpoint.
            p2: Second diameter endpoint.

        Returns:
            The exact circle with segment ``p1-p2`` as a diameter.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)

        Examples:
            >>> c = Circle.from_diameter(Point(0, 0), Point(1, 1))
            >>> (c.center_num.x, c.center_num.y, c.denominator)
            (1, 1, 2)
        """
        cx_num = p1.x + p2.x
        cy_num = p1.y + p2.y
        denominator = 2
        dx = p1.x * denominator - cx_num
        dy = p1.y * denominator - cy_num
        radius_squared_num = dx * dx + dy * dy
        return cls._from_scaled(cx_num, cy_num, denominator, radius_squared_num)

    @classmethod
    def from_three_points(cls, p1: Point, p2: Point, p3: Point) -> 'Circle':
        """
        Construct the circumcircle of three points.

        If the points are collinear, returns the circle using the farthest pair
        as its diameter.

        Args:
            p1: First point.
            p2: Second point.
            p3: Third point.

        Returns:
            The exact circumcircle, or the farthest-pair diameter circle for
            collinear input.

        Time Complexity:
            O(1)

        Space Complexity:
            O(1)

        Examples:
            >>> c = Circle.from_three_points(Point(0, 0), Point(2, 0), Point(0, 2))
            >>> (c.center.x, c.center.y, c.radius_squared_num)
            (1, 1, 2)
        """
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y

        det = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        if det == 0:
            pairs = [(p1, p2), (p1, p3), (p2, p3)]
            far_p1, far_p2 = max(pairs, key=lambda pr: Point.squared_distance(pr[0], pr[1]))
            return cls.from_diameter(far_p1, far_p2)

        c1 = x1 * x1 + y1 * y1
        c2 = x2 * x2 + y2 * y2
        c3 = x3 * x3 + y3 * y3
        cx_num = c1 * (y2 - y3) + c2 * (y3 - y1) + c3 * (y1 - y2)
        cy_num = c1 * (x3 - x2) + c2 * (x1 - x3) + c3 * (x2 - x1)

        denominator = det if det > 0 else -det
        if det < 0:
            cx_num, cy_num = -cx_num, -cy_num

        dx = x1 * denominator - cx_num
        dy = y1 * denominator - cy_num
        radius_squared_num = dx * dx + dy * dy
        return cls._from_scaled(cx_num, cy_num, denominator, radius_squared_num)

    @property
    def center(self) -> Point:
        """
        Return the center when it has integer coordinates.

        Returns:
            Center point.

        Raises:
            ValueError: If the center has non-integer coordinates.

        Time Complexity:
            O(1)

        Examples:
            >>> c = Circle(Point(0, 0), 3)
            >>> (c.center.x, c.center.y)
            (0, 0)
        """
        if self.denominator != 1:
            raise ValueError('center has non-integer coordinates')
        return Point(self.center_num.x, self.center_num.y)

    @property
    def radius(self) -> int:
        """
        Return the radius when it is an integer.

        Returns:
            Integer radius.

        Raises:
            ValueError: If the center or radius is non-integer.

        Time Complexity:
            O(1)

        Examples:
            >>> Circle(Point(0, 0), 3).radius
            3
        """
        if self.denominator != 1:
            raise ValueError('center has non-integer coordinates')
        radius = isqrt(self.radius_squared_num)
        if radius * radius != self.radius_squared_num:
            raise ValueError('radius is non-integer')
        return radius

    def __eq__(self, other: object) -> bool:
        """Check if two circles are equal.

        Args:
            other: The object to compare with.

        Returns:
            True if other is a Circle with the same center and radius, False otherwise.
        """
        if not isinstance(other, Circle):
            return NotImplemented
        return (
            self.center_num == other.center_num
            and self.denominator == other.denominator
            and self.radius_squared_num == other.radius_squared_num
        )

    def contains(self, point: Point) -> bool:
        """
        Check if a point is inside or on the circle.

        Args:
            point: The point to check.

        Returns:
            True if the point is inside or on the circle boundary, False otherwise.

        Time Complexity:
            O(1)

        Examples:
            >>> Circle(Point(0, 0), 5).contains(Point(3, 4))
            True
        """
        dx = point.x * self.denominator - self.center_num.x
        dy = point.y * self.denominator - self.center_num.y
        return dx * dx + dy * dy <= self.radius_squared_num

    def on_circle(self, point: Point) -> bool:
        """
        Check if a point is exactly on the circle boundary.

        Args:
            point: The point to check.

        Returns:
            True if the point is on the circle boundary, False otherwise.

        Time Complexity:
            O(1)

        Examples:
            >>> Circle.from_diameter(Point(0, 0), Point(2, 0)).on_circle(Point(0, 0))
            True
        """
        dx = point.x * self.denominator - self.center_num.x
        dy = point.y * self.denominator - self.center_num.y
        return dx * dx + dy * dy == self.radius_squared_num

    def intersects(self, other: 'Circle') -> bool:
        """
        Check whether the two closed disks overlap.

        Args:
            other: The circle to check intersection with.

        Returns:
            True if the disks share a point, including tangency or one disk
            contained in the other. This does not require their boundaries
            to intersect. Rational centers and non-integer radii created by
            from_diameter or from_three_points are handled exactly.

        Time Complexity:
            O(1)

        Examples:
            >>> Circle(Point(0, 0), 5).intersects(Circle(Point(8, 0), 3))
            True
        """
        d1, d2 = self.denominator, other.denominator
        dx = self.center_num.x * d2 - other.center_num.x * d1
        dy = self.center_num.y * d2 - other.center_num.y * d1
        a = self.radius_squared_num * d2 * d2
        b = other.radius_squared_num * d1 * d1
        gap = dx * dx + dy * dy - a - b
        return gap <= 0 or gap * gap <= 4 * a * b


def manhattan_mst(points: list[Point]) -> tuple[list[tuple[int, int]], int]:
    """
    Compute a minimum spanning tree under Manhattan distance.

    Args:
        points: Integer-coordinate points. Duplicates are allowed, and the
            input list and coordinates are not modified.

    Returns:
        A pair ``(edges, total_weight)``. ``edges`` contains ``n - 1`` pairs of
        point indices (zero pairs for empty input). Empty and singleton
        inputs have total weight zero.

    Time Complexity:
        O(n log n), where n is the number of points

    Space Complexity:
        O(n)

    Examples:
        >>> manhattan_mst([Point(0, 0), Point(1, 0), Point(0, 1)])[1]
        2
    """
    n = len(points)
    if n <= 1:
        return [], 0

    coords = [(p.x, p.y) for p in points]
    empty = (-max(abs(x) + abs(y) for x, y in coords) - 1, -1)
    work = coords[:]
    edges: list[tuple[int, int, int]] = []
    ids = list(range(n))

    for ph in range(4):
        ids.sort(key=lambda i: (work[i][0] + work[i][1], work[i][1]), reverse=True)
        xs = sorted(set(x for x, _ in work))
        fenwick: list[tuple[int, int]] = [empty] * len(xs)

        for idx in ids:
            x, y = work[idx]
            xi = bisect_left(xs, x)
            best = empty
            k = xi + 1
            while k > 0:
                if best[0] <= fenwick[k - 1][0]:
                    best = fenwick[k - 1]
                k -= k & -k
            if best[1] != -1:
                j = best[1]
                w = abs(coords[idx][0] - coords[j][0]) + abs(coords[idx][1] - coords[j][1])
                edges.append((w, idx, j))

            value = x - y
            k = xi + 1
            while k <= len(xs):
                if fenwick[k - 1][0] <= value:
                    fenwick[k - 1] = (value, idx)
                k += k & -k

        work = [(y, x) for x, y in work]
        if ph == 1:
            work = [(x, -y) for x, y in work]

    edges.sort()
    dsu = DisjointSetUnion(n)
    result: list[tuple[int, int]] = []
    total = 0
    for w, u, v in edges:
        if dsu.merge(u, v):
            result.append((u, v))
            total += w
            if len(result) == n - 1:
                break
    return result, total


def euclidean_mst(points: list[Point]) -> list[tuple[int, int]]:
    """
    Compute a minimum spanning tree under Euclidean distance.

    The implementation builds the Delaunay triangulation and then applies
    Kruskal's algorithm to its edges. Edge comparisons use squared distance, so
    no floating-point arithmetic is used.

    Args:
        points: Integer-coordinate points. Duplicates are allowed, and the
            input list and coordinates are not modified.

    Returns:
        ``n - 1`` pairs of point indices, sorted lexicographically, each with
        ``u < v``. Empty and singleton inputs return []. Duplicate points
        are connected using zero-length edges.

    Time Complexity:
        O(n log n), where n is the number of points; the construction is
        deterministic. This counts integer arithmetic operations.
    Space Complexity:
        O(n)

    Examples:
        >>> euclidean_mst([Point(0, 0), Point(1, 0), Point(0, 1)])
        [(0, 1), (0, 2)]
    """
    n = len(points)
    if n <= 1:
        return []

    candidate_edges = delaunay_edges(points)

    def weight(edge: tuple[int, int]) -> int:
        return Point.squared_distance(points[edge[0]], points[edge[1]])

    candidate_edges.sort(key=weight)
    dsu = DisjointSetUnion(n)
    result: list[tuple[int, int]] = []
    for u, v in candidate_edges:
        if dsu.merge(u, v):
            if u > v:
                u, v = v, u
            result.append((u, v))
            if len(result) == n - 1:
                break
    result.sort()
    return result


def delaunay_edges(points: list[Point]) -> list[tuple[int, int]]:
    """
    Return edges of a Delaunay triangulation, plus duplicate-point links.

    Duplicate points are connected to their representative point so that graph
    algorithms such as Euclidean MST can still span all original indices.
    For cocircular points one triangulation is selected; the result does not
    include every edge that could belong to a Delaunay triangulation.
    Collinear distinct points are connected consecutively along their line.

    Args:
        points: Integer-coordinate points in the plane. The input list and
            coordinates are not modified.

    Returns:
        Undirected edge pairs ``(u, v)`` between original point indices, with
        no self-loops or repeated undirected pairs. Edge orientation and
        output order are unspecified. Empty and singleton inputs return [].
        Each duplicate connects to the first input index at that coordinate.

    Time Complexity:
        O(n log n), where n is the number of points; the divide-and-conquer
        construction is deterministic. This counts integer arithmetic
        operations, whose bit cost depends on coordinate magnitudes.
    Space Complexity:
        O(n)

    Examples:
        >>> sorted(tuple(sorted(edge)) for edge in delaunay_edges([Point(0, 0), Point(1, 0), Point(0, 1)]))
        [(0, 1), (0, 2), (1, 2)]
    """
    return _DelaunayTriangulation(points).get_edges()


class _DelaunayTriangulation:
    __slots__ = ('pos_x', 'pos_y', 'edge_to', 'edge_ccw', 'edge_cw', 'edge_rev', 'edge_enabled', 'open_address', 'mappings')

    def __init__(self, points: list[Point]) -> None:
        self.pos_x = [p.x for p in points]
        self.pos_y = [p.y for p in points]
        self.edge_to: list[int] = []
        self.edge_ccw: list[int] = []
        self.edge_cw: list[int] = []
        self.edge_rev: list[int] = []
        self.edge_enabled: list[bool] = []
        self.open_address: list[int] = []
        self.mappings = list(range(len(points)))
        self._solve()

    def _get_open_address(self) -> int:
        if self.open_address:
            return self.open_address.pop()
        self.edge_to.append(-1)
        self.edge_ccw.append(-1)
        self.edge_cw.append(-1)
        self.edge_rev.append(-1)
        self.edge_enabled.append(False)
        return len(self.edge_to) - 1

    def _new_edge(self, u: int, v: int) -> tuple[int, int]:
        euv = self._get_open_address()
        evu = self._get_open_address()
        self.edge_ccw[euv] = self.edge_cw[euv] = euv
        self.edge_ccw[evu] = self.edge_cw[evu] = evu
        self.edge_to[euv] = v
        self.edge_to[evu] = u
        self.edge_rev[euv] = evu
        self.edge_rev[evu] = euv
        self.edge_enabled[euv] = True
        self.edge_enabled[evu] = True
        return euv, evu

    def _erase_single_edge(self, e: int) -> None:
        eccw = self.edge_ccw[e]
        ecw = self.edge_cw[e]
        self.edge_cw[eccw] = ecw
        self.edge_ccw[ecw] = eccw
        self.edge_enabled[e] = False

    def _erase_edge_bidirectional(self, e: int) -> None:
        rev = self.edge_rev[e]
        self._erase_single_edge(e)
        self._erase_single_edge(rev)
        self.open_address.append(e)
        self.open_address.append(rev)

    def _insert_ccw_after(self, e: int, x: int) -> None:
        xccw = self.edge_ccw[x]
        self.edge_ccw[e] = xccw
        self.edge_cw[xccw] = e
        self.edge_cw[e] = x
        self.edge_ccw[x] = e

    def _insert_cw_after(self, e: int, x: int) -> None:
        xcw = self.edge_cw[x]
        self.edge_cw[e] = xcw
        self.edge_ccw[xcw] = e
        self.edge_ccw[e] = x
        self.edge_cw[x] = e

    def _is_ccw(self, a: int, b: int, c: int) -> int:
        abx = self.pos_x[b] - self.pos_x[a]
        aby = self.pos_y[b] - self.pos_y[a]
        acx = self.pos_x[c] - self.pos_x[a]
        acy = self.pos_y[c] - self.pos_y[a]
        cross = abx * acy - aby * acx
        return (cross > 0) - (cross < 0)

    def _in_circle(self, a: int, b: int, c: int, d: int) -> bool:
        ax = self.pos_x[a] - self.pos_x[d]
        ay = self.pos_y[a] - self.pos_y[d]
        bx = self.pos_x[b] - self.pos_x[d]
        by = self.pos_y[b] - self.pos_y[d]
        cx = self.pos_x[c] - self.pos_x[d]
        cy = self.pos_y[c] - self.pos_y[d]
        bxc = bx * cy - by * cx
        cxa = cx * ay - cy * ax
        axb = ax * by - ay * bx
        an = ax * ax + ay * ay
        bn = bx * bx + by * by
        cn = cx * cx + cy * cy
        return bxc * an + cxa * bn + axb * cn > 0

    def _go_next(self, ea: int) -> tuple[int, int]:
        ap = self.edge_to[ea]
        eap = self.edge_ccw[self.edge_rev[ea]]
        return ap, eap

    def _go_prev(self, ea: int) -> tuple[int, int]:
        ap = self.edge_to[self.edge_cw[ea]]
        eap = self.edge_rev[self.edge_cw[ea]]
        return ap, eap

    def _go_bottom(self, a: int, ea: int, b: int, eb: int) -> tuple[int, int, int, int]:
        while True:
            ap, eap = self._go_prev(ea)
            if self._is_ccw(b, a, ap) > 0:
                a, ea = ap, eap
                continue
            bp, ebp = self._go_next(eb)
            if self._is_ccw(a, b, bp) < 0:
                b, eb = bp, ebp
                continue
            break
        return a, ea, b, eb

    def _get_maximum(self, a: int, ea: int, to_min: bool) -> tuple[int, int]:
        ans = (a, ea)
        p, ep = a, ea
        while True:
            p, ep = self._go_next(ep)
            if to_min:
                ans = min(ans, (p, ep))
            else:
                ans = max(ans, (p, ep))
            if ep == ea:
                break
        return ans

    def _dfs(self, a: int, ea: int, b: int, eb: int) -> tuple[int, int]:
        a, ea = self._get_maximum(a, ea, False)
        b, eb = self._get_maximum(b, eb, True)
        al, eal, bl, ebl = self._go_bottom(a, ea, b, eb)
        bu, ebu, au, eau = self._go_bottom(b, eb, a, ea)
        ebl = self.edge_cw[ebl]
        ebu = self.edge_cw[ebu]

        abl, bal = self._new_edge(al, bl)
        self._insert_cw_after(abl, eal)
        self._insert_ccw_after(bal, ebl)
        if al == au:
            eau = abl
        if bl == bu:
            ebu = bal

        ap, eap = al, eal
        bp, ebp = bl, ebl
        while ap != au or bp != bu:
            a2 = self.edge_to[eap]
            b2 = self.edge_to[ebp]
            nxeap = self.edge_ccw[eap]
            nxebp = self.edge_cw[ebp]

            if eap != eau and nxeap != abl:
                a1 = self.edge_to[nxeap]
                if self._in_circle(ap, bp, a2, a1):
                    self._erase_edge_bidirectional(eap)
                    eap = nxeap
                    continue

            if ebp != ebu and nxebp != bal:
                b1 = self.edge_to[nxebp]
                if self._in_circle(b2, ap, bp, b1):
                    self._erase_edge_bidirectional(ebp)
                    ebp = nxebp
                    continue

            choose_a = ebp == ebu
            if eap != eau and ebp != ebu:
                if self._is_ccw(ap, bp, b2) < 0:
                    choose_a = True
                elif self._is_ccw(a2, ap, bp) < 0:
                    choose_a = False
                else:
                    choose_a = self._in_circle(ap, bp, b2, a2)

            if choose_a:
                nxeap = self.edge_ccw[self.edge_rev[eap]]
                hab, hba = self._new_edge(a2, bp)
                self._insert_cw_after(hab, nxeap)
                self._insert_ccw_after(hba, ebp)
                eap = nxeap
                ap = a2
            else:
                nxebp = self.edge_cw[self.edge_rev[ebp]]
                hba, hab = self._new_edge(b2, ap)
                self._insert_ccw_after(hba, nxebp)
                self._insert_cw_after(hab, eap)
                ebp = nxebp
                bp = b2

        return al, abl

    def _solve_range(self, l: int, r: int) -> tuple[int, int]:
        if r - l == 2:
            uv, _ = self._new_edge(l, l + 1)
            return l, uv
        if r - l == 3:
            u = l
            v = l + 1
            w = l + 2
            uv, vu = self._new_edge(u, v)
            vw, wv = self._new_edge(v, w)
            ccw = self._is_ccw(u, v, w)
            if ccw == 0:
                self._insert_ccw_after(vu, vw)
            if ccw > 0:
                uw, wu = self._new_edge(u, w)
                self._insert_cw_after(uv, uw)
                self._insert_cw_after(vw, vu)
                self._insert_cw_after(wu, wv)
                return u, uv
            if ccw < 0:
                uw, wu = self._new_edge(u, w)
                self._insert_ccw_after(uv, uw)
                self._insert_ccw_after(vw, vu)
                self._insert_ccw_after(wu, wv)
                return v, vu
            return u, uv

        m = (l + r) >> 1
        a, ea = self._solve_range(l, m)
        b, eb = self._solve_range(m, r)
        return self._dfs(a, ea, b, eb)

    def _solve(self) -> None:
        n = len(self.pos_x)
        if n <= 1:
            return

        order = sorted(range(n), key=lambda i: (self.pos_x[i], self.pos_y[i]))
        original_x = self.pos_x
        original_y = self.pos_y
        unique_x: list[int] = []
        unique_y: list[int] = []
        representative: list[int] = []
        mappings = [0] * n

        prev_x: int | None = None
        prev_y: int | None = None
        for i in order:
            x = original_x[i]
            y = original_y[i]
            if prev_x is None or x != prev_x or y != prev_y:
                unique_x.append(x)
                unique_y.append(y)
                representative.append(i)
                mappings[i] = i
                prev_x = x
                prev_y = y
            else:
                mappings[i] = representative[-1]

        self.pos_x = unique_x
        self.pos_y = unique_y
        if len(unique_x) >= 2:
            self._solve_range(0, len(unique_x))

        for e in range(len(self.edge_to)):
            self.edge_to[e] = representative[self.edge_to[e]]
        self.pos_x = original_x
        self.pos_y = original_y
        self.mappings = mappings

    def get_edges(self) -> list[tuple[int, int]]:
        """
        Collect active undirected edges and duplicate-point links.

        Returns:
            A new list of pairs of original point indices.

        Time Complexity:
            O(m + n), where m is the number of stored directed edge slots and n is the number of input points
        """
        res: list[tuple[int, int]] = []
        for e in range(len(self.edge_to)):
            if self.edge_enabled[e]:
                rev = self.edge_rev[e]
                if e < rev:
                    continue
                res.append((self.edge_to[e], self.edge_to[rev]))
        for v, rep in enumerate(self.mappings):
            if v != rep:
                res.append((v, rep))
        return res
