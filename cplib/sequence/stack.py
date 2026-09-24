#!/usr/bin/env python3

from collections.abc import Callable


def matched_interval_areas(text: str, open_char: str = '(', close_char: str = ')', area_func: Callable[[int, int], int] | None = None) -> list[int]:
    """
    Compute merged areas for matched character intervals.

    Each ``close_char`` is matched with the nearest unmatched preceding
    ``open_char``. Intervals contained in a newly matched interval are merged
    into it.

    Args:
        text: Input string.
        open_char: Character that starts an interval.
        close_char: Character that closes an interval.
        area_func: Function receiving ``(left, right)`` matched indices and
            returning the interval area. If omitted, ``right - left`` is used.

    Returns:
        Merged interval areas from left to right.

    Time Complexity:
        O(n)

    Space Complexity:
        O(n)
    """
    if area_func is None:
        def default_area(left: int, right: int) -> int:
            return right - left
        area_func = default_area

    stack: list[int] = []
    intervals: list[tuple[int, int]] = []
    for i, c in enumerate(text):
        if c == open_char:
            stack.append(i)
        elif c == close_char and stack:
            left = stack.pop()
            area = area_func(left, i)
            while intervals and intervals[-1][0] > left:
                area += intervals.pop()[1]
            intervals.append((left, area))
    return [area for _, area in intervals]
