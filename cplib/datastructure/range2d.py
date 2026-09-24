#!/usr/bin/env python3

"""Offline orthogonal range-query helpers on integer grids.

This module provides reusable data structures for two standard competitive
programming tasks:

- point-add rectangle-sum queries
- rectangle-add point-get queries

Both wrappers are built on top of an offline 2D Fenwick tree. All update
coordinates must be known when the structure is created, but after that the
operations themselves are processed online in ``O(log^2 n)`` time.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Iterable, Sequence
from typing import Callable, Generic

from cplib.datastructure.fenwicktree import FenwickTree
from cplib.tools.type import ValueT, ActionT

__all__ = [
    "CompressedFenwickTree2D",
    "KDTree2D",
    "LazyKDTree2D",
    "PointAddRectangleSum",
    "RectangleAddPointGet",
    "static_rectangle_union_area",
    "static_rectangle_add_rectangle_sum",
]


class CompressedFenwickTree2D:
    """
    Offline 2D Fenwick tree on sparse integer coordinates.

    The structure registers every point that may ever receive an update, then
    supports point updates together with prefix-sum queries. Prefix queries can
    be issued against arbitrary coordinate thresholds; the queried coordinates
    do not need to be registered in advance. Coordinates and weights may be
    arbitrary integers; bounds count integer arithmetic operations. Duplicate
    registrations refer to one point. Here k is the number of input points.
    Construction sorts by y once, then distributes already sorted coordinates
    to Fenwick nodes, avoiding a separate sort at each node.

    Space Complexity:
        O(k log k)

    Examples:
        >>> bit = CompressedFenwickTree2D([(1, 2), (3, 4), (5, 1)])
        >>> bit.add(1, 2, 7)
        >>> bit.add(3, 4, 5)
        >>> bit.prefix_sum_lt(4, 5)
        12
    """

    __slots__ = ('_data', '_size', '_x_index', '_xs', '_ys', '_registered')

    def __init__(self, points: Iterable[tuple[int, int]]) -> None:
        """
        Initialize the compressed 2D Fenwick tree.

        Args:
            points: Points that may appear in future updates.

        Returns:
            None.

        Time Complexity:
            O(k log k)
        """
        self._registered = set(points)
        self._xs = sorted({x for x, _ in self._registered})
        self._size = len(self._xs)
        self._ys: list[list[int]] = [[] for _ in range(self._size + 1)]
        self._x_index = {x: i + 1 for i, x in enumerate(self._xs)}
        for x, y in sorted(self._registered, key=lambda point: point[1]):
            idx = self._x_index[x]
            while idx <= self._size:
                ys = self._ys[idx]
                if not ys or ys[-1] != y:
                    ys.append(y)
                idx += idx & -idx
        self._data = [[0] * (len(ys) + 1) for ys in self._ys]

    def add(self, x: int, y: int, delta: int) -> None:
        """
        Add ``delta`` to the registered point ``(x, y)``.

        Args:
            x: X-coordinate of the point to update.
            y: Y-coordinate of the point to update.
            delta: Value to add.

        Raises:
            ValueError: If ``(x, y)`` was not registered at construction time.

        Returns:
            None.

        Time Complexity:
            O(log^2 k)
        """

        if (x, y) not in self._registered:
            raise ValueError('point was not registered')
        idx = self._x_index[x]
        while idx <= self._size:
            y_pos = bisect_left(self._ys[idx], y)
            self._add_fenwick(self._data[idx], y_pos + 1, delta)
            idx += idx & -idx

    def prefix_sum_lt(self, x_upper: int, y_upper: int) -> int:
        """
        Return the sum over points with ``x < x_upper`` and ``y < y_upper``.

        Args:
            x_upper: Strict upper bound on the x-coordinate.
            y_upper: Strict upper bound on the y-coordinate.

        Returns:
            Sum of weights in the prefix rectangle.

        Time Complexity:
            O(log^2 k)
        """

        idx = bisect_left(self._xs, x_upper)
        result = 0
        while idx > 0:
            y_pos = bisect_left(self._ys[idx], y_upper)
            result += self._sum_fenwick(self._data[idx], y_pos)
            idx -= idx & -idx
        return result

    def prefix_sum_leq(self, x_max: int, y_max: int) -> int:
        """
        Return the sum over points with ``x <= x_max`` and ``y <= y_max``.

        Args:
            x_max: Inclusive upper bound on the x-coordinate.
            y_max: Inclusive upper bound on the y-coordinate.

        Returns:
            Sum of weights in the prefix rectangle.

        Time Complexity:
            O(log^2 k)
        """

        idx = bisect_right(self._xs, x_max)
        result = 0
        while idx > 0:
            y_pos = bisect_right(self._ys[idx], y_max)
            result += self._sum_fenwick(self._data[idx], y_pos)
            idx -= idx & -idx
        return result

    @staticmethod
    def _add_fenwick(bit: list[int], index: int, delta: int) -> None:
        size = len(bit)
        while index < size:
            bit[index] += delta
            index += index & -index

    @staticmethod
    def _sum_fenwick(bit: Sequence[int], end: int) -> int:
        result = 0
        while end > 0:
            result += bit[end]
            end -= end & -end
        return result


class KDTree2D:
    """
    Static 2D k-d tree with point updates, rectangle-sum queries, and
    rectangle point enumeration.

    The point set is fixed at construction time. Each point keeps an integer
    weight, and the structure supports:

    - updating one point by its original index
    - reading one point weight
    - summing weights on an axis-aligned half-open rectangle

    Duplicate coordinates are allowed because updates are tracked by index
    rather than by coordinate.

    Space Complexity:
        O(n)

    Examples:
        >>> tree = KDTree2D([(1, 2), (3, 4), (2, 1)], [5, 7, 11])
        >>> tree.rectangle_sum(0, 0, 3, 3)
        16
        >>> tree.set(0, 13)
        >>> tree.get(0)
        13
    """

    __slots__ = (
        "_left",
        "_max_x",
        "_max_y",
        "_min_x",
        "_min_y",
        "_node_count",
        "_node_point",
        "_parent",
        "_point_node",
        "_point_values",
        "_points",
        "_right",
        "_root",
        "_sum",
    )

    def __init__(self, points: Iterable[tuple[int, int]], values: Iterable[int] | None = None) -> None:
        """
        Build a static k-d tree on the given points.

        Args:
            points: Point coordinates.
            values: Optional initial weights.

        Returns:
            None.

        Raises:
            ValueError: If ``points`` and ``values`` have different lengths.

        Time Complexity:
            O(n log^2 n)
        """
        self._points = list(points)
        n = len(self._points)
        if values is None:
            self._point_values = [0] * n
        else:
            self._point_values = list(values)
            if len(self._point_values) != n:
                raise ValueError("points and values must have the same length")

        self._left = [-1] * n
        self._right = [-1] * n
        self._min_x = [0] * n
        self._max_x = [0] * n
        self._min_y = [0] * n
        self._max_y = [0] * n
        self._sum = [0] * n
        self._node_point = [-1] * n
        self._parent = [-1] * n
        self._point_node = [-1] * n
        self._node_count = 0
        self._root = -1 if n == 0 else self._build(list(range(n)), 0)

    def _build(self, indices: list[int], depth: int) -> int:
        axis = depth & 1
        if axis == 0:
            indices.sort(key=lambda i: (self._points[i][0], self._points[i][1], i))
        else:
            indices.sort(key=lambda i: (self._points[i][1], self._points[i][0], i))

        mid = len(indices) >> 1
        point_id = indices[mid]
        node = self._node_count
        self._node_count += 1
        self._node_point[node] = point_id
        self._point_node[point_id] = node

        left_node = -1
        if mid > 0:
            left_node = self._build(indices[:mid], depth + 1)
            self._parent[left_node] = node
        right_node = -1
        if mid + 1 < len(indices):
            right_node = self._build(indices[mid + 1 :], depth + 1)
            self._parent[right_node] = node

        self._left[node] = left_node
        self._right[node] = right_node
        self._pull(node, point_id)
        return node

    def _pull(self, node: int, point_id: int) -> None:
        x, y = self._points[point_id]
        min_x = max_x = x
        min_y = max_y = y
        total = self._point_values[point_id]

        left_node = self._left[node]
        if left_node != -1:
            min_x = min(min_x, self._min_x[left_node])
            max_x = max(max_x, self._max_x[left_node])
            min_y = min(min_y, self._min_y[left_node])
            max_y = max(max_y, self._max_y[left_node])
            total += self._sum[left_node]

        right_node = self._right[node]
        if right_node != -1:
            min_x = min(min_x, self._min_x[right_node])
            max_x = max(max_x, self._max_x[right_node])
            min_y = min(min_y, self._min_y[right_node])
            max_y = max(max_y, self._max_y[right_node])
            total += self._sum[right_node]

        self._min_x[node] = min_x
        self._max_x[node] = max_x
        self._min_y[node] = min_y
        self._max_y[node] = max_y
        self._sum[node] = total

    def get(self, point_id: int) -> int:
        """
        Return the current weight of one point.

        Args:
            point_id: Original index of the point in the construction order.

        Returns:
            Weight stored at the point.

        Raises:
            IndexError: If point_id is outside [0, n).

        Time Complexity:
            O(1)
        """
        if not 0 <= point_id < len(self._points):
            raise IndexError('point index out of range')
        return self._point_values[point_id]

    def set(self, point_id: int, value: int) -> None:
        """
        Set the weight of one point.

        Args:
            point_id: Original index of the point in the construction order.
            value: New weight of the point.

        Returns:
            None.

        Raises:
            IndexError: If point_id is outside [0, n).

        Time Complexity:
            O(log n)
        """
        if not 0 <= point_id < len(self._points):
            raise IndexError('point index out of range')
        self._point_values[point_id] = value
        node = self._point_node[point_id]
        while node != -1:
            self._pull(node, self._node_point[node])
            node = self._parent[node]

    def rectangle_sum(self, left: int, down: int, right: int, up: int) -> int:
        """
        Return the sum on the half-open rectangle ``[left, right) x [down, up)``.

        If left >= right or down >= up, the rectangle is empty.

        Args:
            left: Left boundary of the rectangle.
            down: Lower boundary of the rectangle.
            right: Right boundary of the rectangle.
            up: Upper boundary of the rectangle.

        Returns:
            Sum of all point weights inside the rectangle.

        Time Complexity:
            O(n)
        """
        if self._root == -1:
            return 0
        total = 0
        stack = [self._root]
        while stack:
            node = stack.pop()
            if self._max_x[node] < left or right <= self._min_x[node] or self._max_y[node] < down or up <= self._min_y[node]:
                continue
            if left <= self._min_x[node] and self._max_x[node] < right and down <= self._min_y[node] and self._max_y[node] < up:
                total += self._sum[node]
                continue

            point_id = self._node_point[node]
            x, y = self._points[point_id]
            if left <= x < right and down <= y < up:
                total += self._point_values[point_id]
            left_node = self._left[node]
            if left_node != -1:
                stack.append(left_node)
            right_node = self._right[node]
            if right_node != -1:
                stack.append(right_node)
        return total

    def rectangle_indices(self, left: int, down: int, right: int, up: int) -> list[int]:
        """
        Return original point indices inside a half-open rectangle.

        If left >= right or down >= up, the rectangle is empty.

        Args:
            left: Left boundary of the rectangle.
            down: Lower boundary of the rectangle.
            right: Right boundary of the rectangle.
            up: Upper boundary of the rectangle.

        Returns:
            Original point indices whose coordinates are in
            ``[left, right) x [down, up)``. The order is unspecified.

        Time Complexity:
            O(n) in the worst case.
        """
        if self._root == -1:
            return []
        result: list[int] = []
        stack = [self._root]
        while stack:
            node = stack.pop()
            if self._max_x[node] < left or right <= self._min_x[node] or self._max_y[node] < down or up <= self._min_y[node]:
                continue

            point_id = self._node_point[node]
            x, y = self._points[point_id]
            if left <= x < right and down <= y < up:
                result.append(point_id)
            left_node = self._left[node]
            if left_node != -1:
                stack.append(left_node)
            right_node = self._right[node]
            if right_node != -1:
                stack.append(right_node)
        return result


class LazyKDTree2D(Generic[ValueT, ActionT]):
    """
    Static 2D k-d tree with lazy rectangle updates and rectangle queries.

    The point set is fixed at construction time. Each point stores a value of
    type ``ValueT``, and the tree stores one aggregate for every subtree. Rectangle
    updates are propagated lazily using values of type ``ActionT``.

    This is the 2D counterpart of a lazy segment tree on a static point set.
    It is suitable when all points that may ever exist are known in advance.
    Duplicate coordinates remain distinct points addressed by input index.
    Noncommutative aggregates follow the fixed k-d tree preorder, consistently
    for full and partial subtree queries. Complexity assumes O(1) callbacks
    and fixed-size values and actions. Construction recursion has O(log n)
    depth because each median split halves the point count.

    Space Complexity:
        O(n)
    """

    __slots__ = (
        "_count",
        "_e",
        "_id",
        "_lazy",
        "_left",
        "_mapping_prod",
        "_mapping_value",
        "_max_x",
        "_max_y",
        "_min_x",
        "_min_y",
        "_node_count",
        "_node_point",
        "_op",
        "_parent",
        "_point_node",
        "_point_values",
        "_points",
        "_prod",
        "_right",
        "_root",
        "_composition",
    )

    def __init__(
        self,
        points: Iterable[tuple[int, int]],
        values: Iterable[ValueT] | None,
        op: Callable[[ValueT, ValueT], ValueT],
        e: ValueT,
        mapping_prod: Callable[[ActionT, ValueT, int], ValueT],
        mapping_value: Callable[[ActionT, ValueT], ValueT],
        composition: Callable[[ActionT, ActionT], ActionT],
        id: ActionT,
    ) -> None:
        """
        Build a static lazy k-d tree on the given points.

        Args:
            points: Point coordinates.
            values: Initial point values in input order; None uses e at each point.
            op: Associative operation combining aggregates in k-d tree preorder.
                Use a commutative operation when the aggregate must not depend
                on this spatial ordering.
            e: Identity element of ``op``.
            mapping_prod: mapping_prod(action, aggregate, count) must equal
                folding mapping_value(action, value) over the count points.
            mapping_value: Applies a lazy value to one point value.
            composition: composition(new, old) applies old first, then new;
                its action must agree with successive mapping_value calls.
            id: Identity action, recognizable by equality. Callbacks must
                not mutate their inputs, and applying id must change nothing.

        Returns:
            None.

        Raises:
            ValueError: If ``points`` and ``values`` have different lengths.

        Time Complexity:
            O(n log^2 n)
        """
        self._points = list(points)
        n = len(self._points)
        if values is None:
            self._point_values = [e] * n
        else:
            self._point_values = list(values)
            if len(self._point_values) != n:
                raise ValueError("points and values must have the same length")

        self._op = op
        self._e = e
        self._mapping_prod = mapping_prod
        self._mapping_value = mapping_value
        self._composition = composition
        self._id = id

        self._left = [-1] * n
        self._right = [-1] * n
        self._min_x = [0] * n
        self._max_x = [0] * n
        self._min_y = [0] * n
        self._max_y = [0] * n
        self._prod = [e] * n
        self._lazy = [id] * n
        self._count = [0] * n
        self._node_point = [-1] * n
        self._parent = [-1] * n
        self._point_node = [-1] * n
        self._node_count = 0
        self._root = -1 if n == 0 else self._build(list(range(n)), 0)

    def _build(self, indices: list[int], depth: int) -> int:
        axis = depth & 1
        if axis == 0:
            indices.sort(key=lambda i: (self._points[i][0], self._points[i][1], i))
        else:
            indices.sort(key=lambda i: (self._points[i][1], self._points[i][0], i))

        mid = len(indices) >> 1
        point_id = indices[mid]
        node = self._node_count
        self._node_count += 1
        self._node_point[node] = point_id
        self._point_node[point_id] = node

        left_node = -1
        if mid > 0:
            left_node = self._build(indices[:mid], depth + 1)
            self._parent[left_node] = node
        right_node = -1
        if mid + 1 < len(indices):
            right_node = self._build(indices[mid + 1 :], depth + 1)
            self._parent[right_node] = node

        self._left[node] = left_node
        self._right[node] = right_node
        self._pull(node)
        return node

    def _pull(self, node: int) -> None:
        point_id = self._node_point[node]
        x, y = self._points[point_id]
        min_x = max_x = x
        min_y = max_y = y
        count = 1
        prod = self._point_values[point_id]

        left_node = self._left[node]
        if left_node != -1:
            min_x = min(min_x, self._min_x[left_node])
            max_x = max(max_x, self._max_x[left_node])
            min_y = min(min_y, self._min_y[left_node])
            max_y = max(max_y, self._max_y[left_node])
            count += self._count[left_node]
            prod = self._op(prod, self._prod[left_node])

        right_node = self._right[node]
        if right_node != -1:
            min_x = min(min_x, self._min_x[right_node])
            max_x = max(max_x, self._max_x[right_node])
            min_y = min(min_y, self._min_y[right_node])
            max_y = max(max_y, self._max_y[right_node])
            count += self._count[right_node]
            prod = self._op(prod, self._prod[right_node])

        self._min_x[node] = min_x
        self._max_x[node] = max_x
        self._min_y[node] = min_y
        self._max_y[node] = max_y
        self._count[node] = count
        self._prod[node] = prod

    def _all_apply(self, node: int, lazy_value: ActionT) -> None:
        self._prod[node] = self._mapping_prod(lazy_value, self._prod[node], self._count[node])
        point_id = self._node_point[node]
        self._point_values[point_id] = self._mapping_value(lazy_value, self._point_values[point_id])
        self._lazy[node] = self._composition(lazy_value, self._lazy[node])

    def _push(self, node: int) -> None:
        lazy_value = self._lazy[node]
        if lazy_value == self._id:
            return
        left_node = self._left[node]
        if left_node != -1:
            self._all_apply(left_node, lazy_value)
        right_node = self._right[node]
        if right_node != -1:
            self._all_apply(right_node, lazy_value)
        self._lazy[node] = self._id

    def get(self, point_id: int) -> ValueT:
        """
        Return the current value of one point.

        Args:
            point_id: Original index of the point in the construction order.

        Returns:
            Current value stored at the point.

        Raises:
            IndexError: If point_id is outside [0, n).

        Time Complexity:
            O(log n)
        """
        if not 0 <= point_id < len(self._points):
            raise IndexError('point index out of range')
        node = self._point_node[point_id]
        path: list[int] = []
        while node != -1:
            path.append(node)
            node = self._parent[node]
        for current in reversed(path):
            self._push(current)
        return self._point_values[point_id]

    def set(self, point_id: int, value: ValueT) -> None:
        """
        Set the value of one point.

        Args:
            point_id: Original index of the point in the construction order.
            value: New point value.

        Returns:
            None.

        Raises:
            IndexError: If point_id is outside [0, n).

        Time Complexity:
            O(log n)
        """
        if not 0 <= point_id < len(self._points):
            raise IndexError('point index out of range')
        node = self._point_node[point_id]
        path: list[int] = []
        current = node
        while current != -1:
            path.append(current)
            current = self._parent[current]
        for current in reversed(path):
            self._push(current)
        self._point_values[point_id] = value
        for current in path:
            self._pull(current)

    def rectangle_apply(self, left: int, down: int, right: int, up: int, lazy_value: ActionT) -> None:
        """
        Apply one lazy update on a half-open rectangle.

        If left >= right or down >= up, the rectangle is empty.

        Args:
            left: Left boundary.
            down: Lower boundary.
            right: Right boundary.
            up: Upper boundary.
            lazy_value: Update to apply.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        if self._root == -1:
            return
        stack: list[tuple[int, int]] = [(self._root, 0)]
        while stack:
            node, state = stack.pop()
            if state == 1:
                self._pull(node)
                continue
            if self._max_x[node] < left or right <= self._min_x[node] or self._max_y[node] < down or up <= self._min_y[node]:
                continue
            if left <= self._min_x[node] and self._max_x[node] < right and down <= self._min_y[node] and self._max_y[node] < up:
                self._all_apply(node, lazy_value)
                continue

            self._push(node)
            stack.append((node, 1))
            point_id = self._node_point[node]
            x, y = self._points[point_id]
            if left <= x < right and down <= y < up:
                self._point_values[point_id] = self._mapping_value(lazy_value, self._point_values[point_id])
            right_node = self._right[node]
            if right_node != -1:
                stack.append((right_node, 0))
            left_node = self._left[node]
            if left_node != -1:
                stack.append((left_node, 0))

    def rectangle_prod(self, left: int, down: int, right: int, up: int) -> ValueT:
        """
        Aggregate values on a half-open rectangle.

        If left >= right or down >= up, the rectangle is empty.

        Args:
            left: Left boundary.
            down: Lower boundary.
            right: Right boundary.
            up: Upper boundary.

        Returns:
            Aggregate of covered point values in k-d tree preorder (node,
            left subtree, right subtree), not the original input order.
            Returns e for an empty rectangle.

        Time Complexity:
            O(n)
        """
        if self._root == -1:
            return self._e
        res = self._e
        stack = [self._root]
        while stack:
            node = stack.pop()
            if self._max_x[node] < left or right <= self._min_x[node] or self._max_y[node] < down or up <= self._min_y[node]:
                continue
            if left <= self._min_x[node] and self._max_x[node] < right and down <= self._min_y[node] and self._max_y[node] < up:
                res = self._op(res, self._prod[node])
                continue
            self._push(node)
            point_id = self._node_point[node]
            x, y = self._points[point_id]
            if left <= x < right and down <= y < up:
                res = self._op(res, self._point_values[point_id])
            right_node = self._right[node]
            if right_node != -1:
                stack.append(right_node)
            left_node = self._left[node]
            if left_node != -1:
                stack.append(left_node)
        return res


class PointAddRectangleSum:
    """
    Sparse point-add rectangle-sum data structure.

    This wrapper preprocesses every point that may ever be updated and then
    supports:

    - adding a value to one point
    - querying the sum on an axis-aligned half-open rectangle

    Space Complexity:
        O(k log k)

    Examples:
        >>> ds = PointAddRectangleSum([(1, 2), (3, 4), (5, 6)])
        >>> ds.add_point(1, 2, 10)
        >>> ds.add_point(3, 4, 7)
        >>> ds.rectangle_sum(0, 0, 4, 5)
        17
    """

    def __init__(self, points: Iterable[tuple[int, int]]) -> None:
        """
        Initialize the point-add rectangle-sum structure.

        Args:
            points: Points that may appear in future updates.

        Returns:
            None.

        Time Complexity:
            O(k log k)
        """
        self._bit = CompressedFenwickTree2D(points)

    def add_point(self, x: int, y: int, delta: int) -> None:
        """
        Add ``delta`` to the point ``(x, y)``.

        Args:
            x: X-coordinate of the updated point.
            y: Y-coordinate of the updated point.
            delta: Value to add to the point.

        Returns:
            None.

        Raises:
            ValueError: If (x, y) was not registered. The structure is unchanged.

        Time Complexity:
            O(log^2 k)
        """

        self._bit.add(x, y, delta)

    def rectangle_sum(self, left: int, down: int, right: int, up: int) -> int:
        """
        Return the sum on the half-open rectangle ``[left, right) x [down, up)``.

        If left >= right or down >= up, the rectangle is empty.

        Args:
            left: Left boundary of the rectangle.
            down: Lower boundary of the rectangle.
            right: Right boundary of the rectangle.
            up: Upper boundary of the rectangle.

        Returns:
            Sum of all point weights inside the rectangle.

        Time Complexity:
            O(log^2 k)
        """

        if left >= right or down >= up:
            return 0
        return self._bit.prefix_sum_lt(right, up) - self._bit.prefix_sum_lt(left, up) - self._bit.prefix_sum_lt(right, down) + self._bit.prefix_sum_lt(left, down)


class RectangleAddPointGet:
    """
    Sparse rectangle-add point-get data structure.

    The structure preprocesses every rectangle corner that may appear in future
    updates and then supports:

    - adding a value to every integer point in a half-open rectangle
    - querying the value at one point

    The implementation uses a 2D difference array on top of
    :class:`CompressedFenwickTree2D`.

    Space Complexity:
        O(k log k)

    Examples:
        >>> ds = RectangleAddPointGet([(1, 1, 4, 3), (0, 0, 2, 2)])
        >>> ds.add_rectangle(1, 1, 4, 3, 5)
        >>> ds.add_rectangle(0, 0, 2, 2, 2)
        >>> ds.point_get(1, 1)
        7
    """

    def __init__(self, rectangles: Iterable[tuple[int, int, int, int]]) -> None:
        """
        Initialize the rectangle-add point-get structure.

        Args:
            rectangles: Rectangles that may appear in future updates.

        Returns:
            None.

        Time Complexity:
            O(k log k)
        """
        self._corners: set[tuple[int, int]] = set()
        for left, down, right, up in rectangles:
            self._corners.update(((left, down), (left, up), (right, down), (right, up)))
        self._bit = CompressedFenwickTree2D(self._corners)

    def add_rectangle(self, left: int, down: int, right: int, up: int, delta: int) -> None:
        """
        Add ``delta`` to every point in ``[left, right) x [down, up)``.

        If left >= right or down >= up, the rectangle is empty.

        Args:
            left: Left boundary of the rectangle.
            down: Lower boundary of the rectangle.
            right: Right boundary of the rectangle.
            up: Upper boundary of the rectangle.
            delta: Value to add to all covered points.

        Returns:
            None.

        Raises:
            ValueError: If a corner of a nonempty rectangle was not registered.
                No corner is updated on failure. Any rectangle composed of
                registered corners is accepted.

        Time Complexity:
            O(log^2 k)
        """
        if left >= right or down >= up:
            return
        corners = ((left, down), (left, up), (right, down), (right, up))
        if any(point not in self._corners for point in corners):
            raise ValueError('rectangle corners were not registered')
        self._bit.add(left, down, delta)
        self._bit.add(left, up, -delta)
        self._bit.add(right, down, -delta)
        self._bit.add(right, up, delta)

    def point_get(self, x: int, y: int) -> int:
        """
        Return the accumulated value at the point ``(x, y)``.

        Args:
            x: X-coordinate of the query point.
            y: Y-coordinate of the query point.

        Returns:
            Value at the point after all processed rectangle updates.

        Time Complexity:
            O(log^2 k)
        """
        return self._bit.prefix_sum_leq(x, y)


def static_rectangle_union_area(rectangles: Iterable[tuple[int, int, int, int]]) -> int:
    """
    Return the area covered by at least one half-open rectangle.

    Args:
        rectangles: Rectangles ``(left, down, right, up)``.

    Returns:
        Total area of the union of the rectangles. Empty rectangles
        (left >= right or down >= up) are ignored.

    Time Complexity:
        O(k + n log(n + 1)), where k is the input rectangle count and n
        is the number of nonempty rectangles.

    Space Complexity:
        O(n)
    """
    events: list[tuple[int, int, int, int]] = []
    ys: list[int] = []
    for left, down, right, up in rectangles:
        if left >= right or down >= up:
            continue
        events.append((left, 1, down, up))
        events.append((right, -1, down, up))
        ys.append(down)
        ys.append(up)

    if not events:
        return 0

    ys = sorted(set(ys))
    y_index = {y: i for i, y in enumerate(ys)}
    segment_count = len(ys) - 1
    size = 1
    while size < segment_count:
        size <<= 1

    cover = [0] * (2 * size)
    length = [0] * (2 * size)

    def pull(node: int, left: int, right: int) -> None:
        if cover[node] > 0:
            length[node] = ys[right] - ys[left]
        elif node >= size:
            length[node] = 0
        else:
            length[node] = length[node << 1] + length[node << 1 | 1]

    def add(node: int, left: int, right: int, query_left: int, query_right: int, delta: int) -> None:
        if query_right <= left or right <= query_left:
            return
        if query_left <= left and right <= query_right:
            cover[node] += delta
            pull(node, left, right)
            return
        mid = (left + right) >> 1
        add(node << 1, left, mid, query_left, query_right, delta)
        add(node << 1 | 1, mid, right, query_left, query_right, delta)
        pull(node, left, right)

    events.sort()
    area = 0
    prev_x = events[0][0]
    for x, delta, down, up in events:
        area += length[1] * (x - prev_x)
        add(1, 0, size, y_index[down], y_index[up], delta)
        prev_x = x
    return area


def static_rectangle_add_rectangle_sum(rectangles: Iterable[tuple[int, int, int, int, int]], queries: Iterable[tuple[int, int, int, int]], mod: int | None = None) -> list[int]:
    """
    Solve static rectangle-add rectangle-sum queries offline.

    Each update adds ``weight`` to every point in the half-open rectangle
    ``[left, right) x [down, up)``. Each query asks for the total weight inside
    another half-open rectangle. Updates and queries are given in separate
    batches, so the whole problem can be processed by one sweep-line over the
    y-axis. Coordinates are integers, so the covered lattice-point count
    equals the rectangle area. Empty updates and queries (left >= right or
    down >= up) contribute zero. Integer arithmetic is exact when mod is None.

    Args:
        rectangles: Update rectangles ``(left, down, right, up, weight)``.
        queries: Query rectangles ``(left, down, right, up)``.
        mod: Optional positive modulus applied to all arithmetic.

    Returns:
        list[int]: Rectangle sums in the same order as ``queries``.

    Raises:
        ValueError: If mod is nonpositive.

    Time Complexity:
        O((n + q) log (n + q))

    Space Complexity:
        O(n + q)
    """

    if mod is not None and mod <= 0:
        raise ValueError('mod must be positive')

    def normalize(value: int) -> int:
        if mod is None:
            return value
        return value % mod

    add_events: list[tuple[int, int, int, int, int, int]] = []
    xs: list[int] = []
    for left, down, right, up, weight in rectangles:
        if left >= right or down >= up:
            continue
        w = normalize(weight)
        corners = (
            (left, down, w),
            (left, up, normalize(-w)),
            (right, down, normalize(-w)),
            (right, up, w),
        )
        for x, y, signed_weight in corners:
            add_events.append(
                (
                    y,
                    x,
                    signed_weight,
                    normalize(-signed_weight * y),
                    normalize(-signed_weight * x),
                    normalize(signed_weight * x * y),
                )
            )
            xs.append(x)

    query_list = list(queries)
    if not add_events:
        return [0] * len(query_list)

    xs = sorted(set(xs))
    bit_a = FenwickTree(len(xs))
    bit_b = FenwickTree(len(xs))
    bit_c = FenwickTree(len(xs))
    bit_d = FenwickTree(len(xs))

    requests: list[tuple[int, int, int, int]] = []
    for query_id, (left, down, right, up) in enumerate(query_list):
        if left >= right or down >= up:
            continue
        requests.append((up, right, query_id, 1))
        requests.append((up, left, query_id, -1))
        requests.append((down, right, query_id, -1))
        requests.append((down, left, query_id, 1))

    add_events.sort()
    requests.sort()
    answers = [0] * len(query_list)
    event_ptr = 0

    for y_upper, x_upper, query_id, sign in requests:
        while event_ptr < len(add_events) and add_events[event_ptr][0] < y_upper:
            _, x, coeff_a, coeff_b, coeff_c, coeff_d = add_events[event_ptr]
            idx = bisect_left(xs, x)
            bit_a.add(idx, coeff_a)
            bit_b.add(idx, coeff_b)
            bit_c.add(idx, coeff_c)
            bit_d.add(idx, coeff_d)
            event_ptr += 1

        x_pos = bisect_left(xs, x_upper)
        value = (
            bit_a.sum(x_pos) * x_upper * y_upper
            + bit_b.sum(x_pos) * x_upper
            + bit_c.sum(x_pos) * y_upper
            + bit_d.sum(x_pos)
        )
        if mod is not None:
            value %= mod
        answers[query_id] += value if sign > 0 else -value
        if mod is not None:
            answers[query_id] %= mod

    if mod is not None:
        return [value % mod for value in answers]
    return answers
