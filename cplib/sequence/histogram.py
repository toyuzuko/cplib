#!/usr/bin/env python3

from collections.abc import Sequence


def largest_rectangle_area(histogram: Sequence[int]) -> int:
    """
    Return the largest rectangle area in a histogram.

    Args:
        histogram: Non-negative bar heights.

    Returns:
        Maximum rectangle area.

    Raises:
        ValueError: If a height is negative.

    Time Complexity:
        O(n), where ``n`` is ``len(histogram)``.

    Space Complexity:
        O(n)
    """
    stack: list[tuple[int, int]] = []
    best = 0
    for i in range(len(histogram) + 1):
        height = histogram[i] if i < len(histogram) else 0
        if height < 0:
            raise ValueError('histogram heights must be non-negative')
        start = i
        while stack and stack[-1][1] > height:
            left, h = stack.pop()
            area = h * (i - left)
            if area > best:
                best = area
            start = left
        if not stack or stack[-1][1] < height:
            stack.append((start, height))
    return best
