#!/usr/bin/env python3

from collections.abc import Callable
from typing import Generic
from cplib.tools.type import ValueT


class Cumulative(Generic[ValueT]):
    """
    Prefix-aggregate structure for static range queries.

    After one linear build pass, the structure answers half-open range queries
    in constant time for any associative operation equipped with a left
    inverse on prefix aggregates.

    Complexity bounds assume O(1) callbacks and fixed-size aggregate values.

    Examples:
        >>> cum = Cumulative(5, 0, lambda a, b: a + b, lambda a, b: a - b)
        >>> cum.build([1, 2, 3, 4, 5])
        >>> cum.prod(1, 4)
        9

    Space Complexity:
        O(n)
    """
    def __init__(self, n: int, init: ValueT, op: Callable[[ValueT, ValueT], ValueT], inv_op: Callable[[ValueT, ValueT], ValueT]) -> None:
        """
        Initialize the prefix aggregates.

        Args:
            n: Number of elements.
            init: Identity element of the aggregation.
            op: Associative binary operation on values.
            inv_op: Recover a range from ``(whole_prefix, removed_prefix)``;
                must satisfy ``inv_op(op(a, b), a) == b``. For a group,
                use ``op(inverse(removed_prefix), whole_prefix)``, not right cancellation.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative.

        Time Complexity:
            O(n)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.init = init
        self.op = op
        self.inv_op = inv_op
        self.cum = [init] * (n + 1)

    def build(self, arr: list[ValueT]) -> None:
        """
        Build the prefix aggregates from ``arr``.

        Args:
            arr: Input array of length ``n``.

        Returns:
            None.

        Raises:
            ValueError: If ``len(arr) != n``; the stored prefixes are unchanged.

        Time Complexity:
            O(n)
        """
        if len(arr) != self.n:
            raise ValueError('array length does not match the initialized size')
        for i in range(self.n):
            self.cum[i + 1] = self.op(self.cum[i], arr[i])

    def prod(self, l: int, r: int) -> ValueT:
        """
        Return the aggregate on ``[l, r)``.

        Args:
            l: Left boundary, inclusive.
            r: Right boundary, exclusive.

        Returns:
            Aggregate of ``arr[l:r]``.

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` does not hold.

        Notes:
            Call ``build`` before querying the input array.

        Time Complexity:
            O(1)
        """
        assert 0 <= l <= r <= self.n  # [l, r)
        return self.inv_op(self.cum[r], self.cum[l])


class CumulativeSum2D:
    """
    2D cumulative sums with constant-time ``rectangle_sum`` queries.

    This structure preprocesses a rectangular grid of integers and then answers
    axis-aligned half-open rectangle sums in ``O(1)`` time.

    Space Complexity:
        O(h * w)

    Examples:
        >>> cum = CumulativeSum2D(2, 3)
        >>> cum.build([[1, 2, 3], [4, 5, 6]])
        >>> cum.rectangle_sum(0, 1, 2, 3)
        16
    """

    def __init__(self, h: int, w: int) -> None:
        """
        Initialize an empty 2D prefix-sum table.

        Args:
            h: Number of rows.
            w: Number of columns.

        Returns:
            None.

        Raises:
            ValueError: If either dimension is negative.

        Time Complexity:
            O(h * w)
        """
        if h < 0 or w < 0:
            raise ValueError('dimensions must be non-negative')
        self.h = h
        self.w = w
        self.cum = [[0] * (w + 1) for _ in range(h + 1)]

    def build(self, grid: list[list[int]]) -> None:
        """
        Build the 2D prefix-sum table.

        Args:
            grid: Integer grid of shape ``h x w``.

        Returns:
            None.

        Raises:
            ValueError: If ``grid`` does not match the initialized shape.

        Time Complexity:
            O(h * w)
        """
        if len(grid) != self.h or any(len(row) != self.w for row in grid):
            raise ValueError('grid shape does not match the initialized size')
        for i in range(self.h):
            row_sum = 0
            cum_i = self.cum[i + 1]
            prev = self.cum[i]
            for j in range(self.w):
                row_sum += grid[i][j]
                cum_i[j + 1] = prev[j + 1] + row_sum

    def rectangle_sum(self, top: int, left: int, bottom: int, right: int) -> int:
        """
        Return the sum on ``[top, bottom) x [left, right)``.

        Args:
            top: Top boundary.
            left: Left boundary.
            bottom: Bottom boundary.
            right: Right boundary.

        Returns:
            Sum of the rectangle.

        Raises:
            AssertionError: If the rectangle is reversed or outside the grid.

        Time Complexity:
            O(1)
        """
        assert 0 <= top <= bottom <= self.h  # [top, bottom)
        assert 0 <= left <= right <= self.w  # [left, right)
        return self.cum[bottom][right] - self.cum[top][right] - self.cum[bottom][left] + self.cum[top][left]


class Imos1D:
    """
    1D difference-array helper for offline range additions.

    The structure supports adding values to half-open intervals and then
    materializing the final array by one cumulative pass.

    Space Complexity:
        O(n)

    Examples:
        >>> imos = Imos1D(5)
        >>> imos.add(1, 4, 2)
        >>> imos.add(2, 5, 3)
        >>> imos.build()
        [0, 2, 5, 5, 3]
    """

    def __init__(self, n: int) -> None:
        """
        Initialize an empty 1D difference table.

        Args:
            n: Number of elements.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative.

        Time Complexity:
            O(n)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.diff = [0] * (n + 1)

    def add(self, left: int, right: int, value: int) -> None:
        """
        Add ``value`` to the interval ``[left, right)``.

        Args:
            left: Left boundary.
            right: Right boundary.
            value: Value to add.

        Returns:
            None.

        Raises:
            AssertionError: If ``0 <= left <= right <= n`` does not hold.

        Time Complexity:
            O(1)
        """
        assert 0 <= left <= right <= self.n
        self.diff[left] += value
        self.diff[right] -= value

    def build(self) -> list[int]:
        """
        Materialize the final array after all interval additions.

        Returns:
            The array after applying all stored updates.

        Notes:
            Does not consume updates. Repeated builds and later additions are supported.

        Time Complexity:
            O(n)
        """
        res = [0] * self.n
        cur = 0
        for i in range(self.n):
            cur += self.diff[i]
            res[i] = cur
        return res


class Imos2D:
    """
    2D difference-array helper for offline rectangle additions.

    The structure supports adding values to half-open rectangles and then
    materializing the final grid by one cumulative pass.

    Space Complexity:
        O(h * w)

    Examples:
        >>> imos = Imos2D(3, 4)
        >>> imos.add(0, 0, 2, 3, 5)
        >>> imos.add(1, 1, 3, 4, 2)
        >>> grid = imos.build()
        >>> grid[1][2]
        7
    """

    def __init__(self, h: int, w: int) -> None:
        """
        Initialize an empty 2D difference table.

        Args:
            h: Number of rows.
            w: Number of columns.

        Returns:
            None.

        Raises:
            ValueError: If either dimension is negative.

        Time Complexity:
            O(h * w)
        """
        if h < 0 or w < 0:
            raise ValueError('dimensions must be non-negative')
        self.h = h
        self.w = w
        self.diff = [[0] * (w + 1) for _ in range(h + 1)]

    def add(self, top: int, left: int, bottom: int, right: int, value: int) -> None:
        """
        Add ``value`` to the rectangle ``[top, bottom) x [left, right)``.

        Args:
            top: Top boundary.
            left: Left boundary.
            bottom: Bottom boundary.
            right: Right boundary.
            value: Value to add.

        Returns:
            None.

        Raises:
            AssertionError: If the rectangle is reversed or outside the grid.

        Time Complexity:
            O(1)
        """
        assert 0 <= top <= bottom <= self.h
        assert 0 <= left <= right <= self.w
        self.diff[top][left] += value
        self.diff[top][right] -= value
        self.diff[bottom][left] -= value
        self.diff[bottom][right] += value

    def build(self) -> list[list[int]]:
        """
        Materialize the final grid after all rectangle additions.

        Returns:
            The ``h x w`` grid after applying all stored updates.

        Notes:
            Does not consume updates. Repeated builds and later additions are supported.

        Time Complexity:
            O(h * w)
        """
        res = [[0] * self.w for _ in range(self.h)]
        for i in range(self.h):
            row_sum = 0
            for j in range(self.w):
                row_sum += self.diff[i][j]
                if i == 0:
                    res[i][j] = row_sum
                else:
                    res[i][j] = res[i - 1][j] + row_sum
        return res
