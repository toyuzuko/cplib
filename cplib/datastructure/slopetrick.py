#!/usr/bin/env python3

"""Slope trick for convex piecewise-linear functions.

This module provides a reusable ``SlopeTrick`` class with:

- one-sided hinge additions such as ``max(x - a, 0)``
- absolute-value additions ``abs(x - a)``
- sliding-window minimum and translation operations
- minimum-value, minimum-interval, and point-evaluation queries

The implementation uses the standard two-heap representation and is intended
for contest-style dynamic programming.
"""

from __future__ import annotations

import heapq

__all__ = ["SlopeTrick"]


class SlopeTrick:
    """
    Maintain a convex piecewise-linear function by slope trick.

    The stored function starts as the constant ``minimum`` on the whole real
    line and supports typical contest operations:

    - add ``max(x - a, 0)``
    - add ``max(a - x, 0)``
    - add ``abs(x - a)``
    - shift the function horizontally
    - take a sliding-window minimum

    Internally the function is represented as:

    ``minimum + sum(max(li - x, 0)) + sum(max(x - ri, 0))``

    where the breakpoints ``li`` and ``ri`` are managed by two heaps with lazy
    offsets. Initially, ``minimum_interval()`` returns ``(None, None)``
    because the minimum is attained on the whole line.

    Here n is the number of hinge breakpoints currently retained. Each
    hinge addition contributes at most one breakpoint, and add_abs adds two.
    Bounds assume constant-time integer arithmetic.

    Space Complexity:
        O(n)

    Examples:
        >>> st = SlopeTrick()
        >>> st.add_abs(3)
        >>> st.add_x_minus_a(5)
        >>> st.minimum()
        0
        >>> st.minimum_interval()
        (3, 3)
    """

    def __init__(self, minimum: int = 0) -> None:
        """
        Initialize the function as a constant.

        Args:
            minimum: Initial constant value on the whole line.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._minimum = minimum
        self._left: list[int] = []
        self._right: list[int] = []
        self._add_left = 0
        self._add_right = 0

    def _push_left(self, value: int) -> None:
        heapq.heappush(self._left, -(value - self._add_left))

    def _push_right(self, value: int) -> None:
        heapq.heappush(self._right, value - self._add_right)

    def _pop_left(self) -> int:
        return -heapq.heappop(self._left) + self._add_left

    def _pop_right(self) -> int:
        return heapq.heappop(self._right) + self._add_right

    def _top_left(self) -> int | None:
        if not self._left:
            return None
        return -self._left[0] + self._add_left

    def _top_right(self) -> int | None:
        if not self._right:
            return None
        return self._right[0] + self._add_right

    def add_const(self, value: int) -> None:
        """
        Add a constant to the stored function.

        Args:
            value: Constant value to add.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._minimum += value

    def add_x_minus_a(self, a: int) -> None:
        """
        Add ``max(x - a, 0)`` to the stored function.

        Args:
            a: Breakpoint of the hinge function.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        left = self._top_left()
        if left is not None and a < left:
            self._minimum += left - a
            self._push_left(a)
            self._push_right(self._pop_left())
        else:
            self._push_right(a)

    def add_a_minus_x(self, a: int) -> None:
        """
        Add ``max(a - x, 0)`` to the stored function.

        Args:
            a: Breakpoint of the hinge function.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        right = self._top_right()
        if right is not None and a > right:
            self._minimum += a - right
            self._push_right(a)
            self._push_left(self._pop_right())
        else:
            self._push_left(a)

    def add_abs(self, a: int) -> None:
        """
        Add ``abs(x - a)`` to the stored function.

        Args:
            a: Center of the absolute-value term.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        self.add_a_minus_x(a)
        self.add_x_minus_a(a)

    def shift(self, delta: int) -> None:
        """
        Translate the function to ``g(x) = f(x - delta)``.

        Args:
            delta: Horizontal shift amount.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._add_left += delta
        self._add_right += delta

    def sliding_window_min(self, left: int, right: int) -> None:
        """
        Replace the function by its sliding-window minimum.

        The new function is:

        ``g(x) = min_{x - right <= y <= x - left} f(y)``

        Args:
            left: Left end of the allowed offset interval.
            right: Right end of the allowed offset interval.

        Raises:
            ValueError: If ``left > right``.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        if left > right:
            raise ValueError("left must be less than or equal to right")
        self._add_left += left
        self._add_right += right

    def prefix_min(self) -> None:
        """
        Replace the function by ``g(x) = min_{y <= x} f(y)``.

        Discard the right heap, removing the increasing part of the function.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self._right.clear()

    def suffix_min(self) -> None:
        """
        Replace the function by ``g(x) = min_{y >= x} f(y)``.

        Discard the left heap, removing the decreasing part of the function.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self._left.clear()

    def minimum(self) -> int:
        """
        Return the minimum value of the stored function.

        Returns:
            Minimum function value.

        Time Complexity:
            O(1)
        """
        return self._minimum

    def minimum_interval(self) -> tuple[int | None, int | None]:
        """
        Return the interval where the minimum value is attained.

        Returns:
            Pair ``(left, right)`` describing the closed interval of minimizers.
            ``None`` means the interval is unbounded on that side.

        Time Complexity:
            O(1)
        """
        return self._top_left(), self._top_right()

    def evaluate(self, x: int) -> int:
        """
        Evaluate the stored function at one point.

        Args:
            x: Query point.

        Returns:
            Exact function value at ``x``.

        Time Complexity:
            O(n)
        """
        value = self._minimum
        for raw in self._left:
            breakpoint = -raw + self._add_left
            if breakpoint > x:
                value += breakpoint - x
        for raw in self._right:
            breakpoint = raw + self._add_right
            if breakpoint < x:
                value += x - breakpoint
        return value
