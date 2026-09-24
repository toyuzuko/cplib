#!/usr/bin/env python3

from collections.abc import Sequence

from cplib.sequence.histogram import largest_rectangle_area


def largest_square_area_in_grid(grid: Sequence[Sequence[int]], available_value: int = 0) -> int:
    """
    Return the largest square area consisting only of one cell value.

    Args:
        grid: Rectangular grid.
        available_value: Cell value treated as usable.

    Returns:
        Maximum square area.

    Raises:
        ValueError: If ``grid`` is not rectangular.

    Time Complexity:
        O(hw), where ``h`` and ``w`` are grid dimensions.

    Space Complexity:
        O(w)
    """
    if not grid:
        return 0
    w = len(grid[0])
    prev = [0] * (w + 1)
    best = 0
    for row in grid:
        if len(row) != w:
            raise ValueError('grid must be rectangular')
        cur = [0] * (w + 1)
        for j, value in enumerate(row, 1):
            if value == available_value:
                side = min(prev[j - 1], prev[j], cur[j - 1]) + 1
                cur[j] = side
                if side > best:
                    best = side
        prev = cur
    return best * best


def count_squares_in_grid(grid: Sequence[Sequence[int]], available_value: int = 0) -> int:
    """
    Count square subgrids consisting only of one cell value.

    Args:
        grid: Rectangular grid.
        available_value: Cell value treated as usable.

    Returns:
        Number of square subgrids.

    Raises:
        ValueError: If ``grid`` is not rectangular.

    Time Complexity:
        O(hw), where ``h`` and ``w`` are grid dimensions.

    Space Complexity:
        O(w)
    """
    if not grid:
        return 0
    w = len(grid[0])
    prev = [0] * (w + 1)
    total = 0
    for row in grid:
        if len(row) != w:
            raise ValueError('grid must be rectangular')
        cur = [0] * (w + 1)
        for j, value in enumerate(row, 1):
            if value == available_value:
                side = min(prev[j - 1], prev[j], cur[j - 1]) + 1
                cur[j] = side
                total += side
        prev = cur
    return total


def largest_rectangle_area_in_grid(grid: Sequence[Sequence[int]], available_value: int = 0) -> int:
    """
    Return the largest rectangle area consisting only of one cell value.

    Args:
        grid: Rectangular grid.
        available_value: Cell value treated as usable.

    Returns:
        Maximum rectangle area.

    Raises:
        ValueError: If ``grid`` is not rectangular.

    Time Complexity:
        O(hw), where ``h`` and ``w`` are grid dimensions.

    Space Complexity:
        O(w)
    """
    if not grid:
        return 0
    w = len(grid[0])
    heights = [0] * w
    best = 0
    for row in grid:
        if len(row) != w:
            raise ValueError('grid must be rectangular')
        for j, value in enumerate(row):
            if value == available_value:
                heights[j] += 1
            else:
                heights[j] = 0
        area = largest_rectangle_area(heights)
        if area > best:
            best = area
    return best


def count_rectangles_in_grid(grid: Sequence[Sequence[int]], available_value: int = 0) -> int:
    """
    Count rectangular subgrids consisting only of one cell value.

    Args:
        grid: Rectangular grid.
        available_value: Cell value treated as usable.

    Returns:
        Number of rectangular subgrids.

    Raises:
        ValueError: If ``grid`` is not rectangular.

    Time Complexity:
        O(hw), where ``h`` and ``w`` are grid dimensions.

    Space Complexity:
        O(w)
    """
    if not grid:
        return 0
    w = len(grid[0])
    heights = [0] * w
    total = 0
    for row in grid:
        if len(row) != w:
            raise ValueError('grid must be rectangular')
        for j, value in enumerate(row):
            if value == available_value:
                heights[j] += 1
            else:
                heights[j] = 0

        stack: list[tuple[int, int]] = []
        row_total = 0
        for height in heights:
            count = 1
            while stack and stack[-1][0] >= height:
                prev_height, prev_count = stack.pop()
                row_total -= prev_height * prev_count
                count += prev_count
            stack.append((height, count))
            row_total += height * count
            total += row_total
    return total
