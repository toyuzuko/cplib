#!/usr/bin/env python3

from bisect import bisect_left
from collections import deque

__all__ = ["LiChaoTree", "MonotoneConvexHullTrick"]

class LiChaoTree:
    """
    Li Chao tree for minimum queries on affine functions.

    A data structure that maintains a set of linear functions and supports
    minimum queries on a fixed set of x-coordinates. Integer coordinates and
    coefficients are unbounded; complexity bounds count integer operations.

    Attributes:
        variables: Copied coordinates, padded by repeating the largest coordinate.
        n: Number of distinct query coordinates.
        size: Internal segment-tree leaf count.

    Examples:
        >>> lichao = LiChaoTree([1, 2, 3, 4, 5])
        >>> lichao.add_line(2, 3)
        >>> lichao.add_line(-1, 10)
        >>> lichao.get_min(3)
        7

    Space Complexity:
        O(n)
    """
    def __init__(self, variables: list[int]) -> None:
        """
        Initialize the tree on a fixed set of x-coordinates.

        Args:
            variables: Strictly increasing query coordinates; an empty list is valid.

        Returns:
            None.

        Raises:
            ValueError: If ``variables`` is not strictly increasing.

        Time Complexity:
            O(n)
        """
        if any(not a < b for a, b in zip(variables, variables[1:])):
            raise ValueError('variables must be sorted')
        self.n = len(variables)
        self.size = 1 << max(0, self.n - 1).bit_length()
        self.variables = variables + [variables[-1]] * (self.size - self.n) if variables else []
        self.a = [0] * (2 * self.size)
        self.b = [0] * (2 * self.size)
        self._used = [False] * (2 * self.size)

    def _findpos(self, x: int) -> tuple[int, bool]:
        p = bisect_left(self.variables, x, 0, self.n)
        if p >= self.n or self.variables[p] != x: return p, False
        return p, True

    def _add(self, a: int, b: int, idx: int, lpos: int, rpos: int) -> None:
        while True:
            if not self._used[idx]:
                self.a[idx], self.b[idx] = a, b
                self._used[idx] = True
                return
            mpos = (lpos + rpos) >> 1
            lx = self.variables[lpos]
            mx = self.variables[mpos]
            rx = self.variables[rpos - 1]
            ai, bi = self.a[idx], self.b[idx]
            lu = a * lx + b < ai * lx + bi
            mu = a * mx + b < ai * mx + bi
            ru = a * rx + b < ai * rx + bi
            if lu and ru:
                self.a[idx], self.b[idx] = a, b
                return
            if not lu and not ru:
                return
            if mu:
                self.a[idx], self.b[idx], a, b = a, b, self.a[idx], self.b[idx]
            if lu != mu:
                rpos = mpos
                idx = 2 * idx
            else:
                lpos = mpos
                idx = 2 * idx + 1

    def add_line(self, a: int, b: int) -> None:
        """
        Add a linear function ax + b to the tree.

        An empty coordinate domain is unchanged.

        Args:
            a: Slope of the line.
            b: Intercept of the line.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        if self.n:
            self._add(a, b, 1, 0, self.size)

    def add_segment(self, a: int, b: int, l: int, r: int) -> None:
        """
        Add a linear function ax + b only for x in [l, r).

        The boundaries need not be registered query coordinates. An empty
        interval or an interval containing no registered coordinate is ignored.

        Args:
            a: Slope of the line segment.
            b: Intercept of the line segment.
            l: Left boundary, inclusive.
            r: Right boundary, exclusive.

        Raises:
            ValueError: If l > r.

        Returns:
            None.

        Time Complexity:
            O(log^2 n)
        """
        if l > r:
            raise ValueError('left boundary must not exceed right boundary')
        lpos, _ = self._findpos(l)
        rpos, _ = self._findpos(r)
        lidx = lpos + self.size
        ridx = rpos + self.size
        sz = 1
        while lidx < ridx:
            if lidx & 1:
                self._add(a, b, lidx, lpos, lpos + sz)
                lidx += 1
                lpos += sz
            if ridx & 1:
                ridx -= 1
                self._add(a, b, ridx, rpos - sz, rpos)
                rpos -= sz
            lidx >>= 1
            ridx >>= 1
            sz <<= 1

    def get_min(self, x: int) -> int | None:
        """
        Get minimum value among all functions at x-coordinate.

        Args:
            x: Query coordinate.

        Returns:
            Minimum value of all stored functions covering ``x``, or ``None``
            if none covers the coordinate. Every integer, including zero and
            values outside the signed 64-bit range, is a valid result.

        Raises:
            AssertionError: If x is not a registered coordinate.

        Time Complexity:
            O(log n)

        Examples:
            >>> tree = LiChaoTree([0, 1, 2])
            >>> tree.get_min(1) is None
            True
            >>> tree.add_segment(0, 2**63 - 1, 1, 2)
            >>> tree.get_min(1)
            9223372036854775807
            >>> tree.get_min(2) is None
            True
        """
        p, f = self._findpos(x)
        assert f  # x is one of the registered coordinates
        idx = p + self.size
        res: int | None = None
        while idx:
            if self._used[idx]:
                value = self.a[idx] * x + self.b[idx]
                if res is None or value < res:
                    res = value
            idx >>= 1
        return res


class MonotoneConvexHullTrick:
    """
    Deque-based convex hull trick for monotone slopes and monotone queries.

    This structure maintains linear functions ``f(x) = a x + b`` and supports
    minimum queries under two monotonicity assumptions:

    - lines are added in monotone slope order
    - query x-coordinates are asked in monotone order

    Under these assumptions, both insertion and query run in amortized ``O(1)``
    time, which is typically faster than :class:`LiChaoTree` when the
    monotonicity conditions are available.

    Space Complexity:
        O(n)

    Examples:
        >>> cht = MonotoneConvexHullTrick()
        >>> cht.add_line(3, 1)
        >>> cht.add_line(1, 5)
        >>> cht.get_min(0)
        1
    """

    def __init__(self, slope_increasing: bool = False, query_increasing: bool = True) -> None:
        """
        Initialize the monotone convex hull trick.

        Args:
            slope_increasing: Whether inserted slopes are monotone increasing.
            query_increasing: Whether query points are monotone increasing.

        Returns:
            None.

        Raises:
            ValueError: If the configured slope and query directions are incompatible.

        Time Complexity:
            O(1)
        """
        if slope_increasing == query_increasing:
            raise ValueError('deque-based min CHT requires opposite slope/query directions')
        self.lines: deque[tuple[int, int]] = deque()
        self.slope_increasing = slope_increasing
        self.query_increasing = query_increasing
        self._last_x: int | None = None

    @staticmethod
    def _value(line: tuple[int, int], x: int) -> int:
        a, b = line
        return a * x + b

    @staticmethod
    def _is_redundant(line1: tuple[int, int], line2: tuple[int, int], line3: tuple[int, int]) -> bool:
        a1, b1 = line1
        a2, b2 = line2
        a3, b3 = line3
        return (b3 - b1) * (a1 - a2) <= (b2 - b1) * (a1 - a3)

    def add_line(self, a: int, b: int) -> None:
        """
        Add a line ``f(x) = a x + b``.

        Args:
            a: Slope of the line.
            b: Intercept of the line.

        Returns:
            None.

        Raises:
            ValueError: If the slope monotonicity is violated.

        Time Complexity:
            Amortized O(1)
        """
        normalized_a = a if self.query_increasing else -a
        if self.lines:
            last_a, last_b = self.lines[-1]
            if normalized_a > last_a:
                raise ValueError('slopes must follow the configured monotone order')
            if normalized_a == last_a:
                if b >= last_b:
                    return
                self.lines.pop()

        new_line = (normalized_a, b)
        while len(self.lines) >= 2 and self._is_redundant(self.lines[-2], self.lines[-1], new_line):
            self.lines.pop()
        self.lines.append(new_line)

    def get_min(self, x: int) -> int:
        """
        Return the minimum value at x.

        Args:
            x: Query point.

        Returns:
            Minimum value among all stored lines at ``x``.

        Raises:
            ValueError: If no line exists or if query monotonicity is violated.

        Time Complexity:
            Amortized O(1)
        """
        if not self.lines:
            raise ValueError('no line has been added')
        if self._last_x is not None:
            if self.query_increasing:
                if x < self._last_x:
                    raise ValueError('query x-coordinates must be monotone increasing')
            else:
                if x > self._last_x:
                    raise ValueError('query x-coordinates must be monotone decreasing')
        self._last_x = x

        normalized_x = x if self.query_increasing else -x
        while len(self.lines) >= 2 and self._value(self.lines[0], normalized_x) >= self._value(self.lines[1], normalized_x):
            self.lines.popleft()
        return self._value(self.lines[0], normalized_x)
