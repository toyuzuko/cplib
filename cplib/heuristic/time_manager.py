"""Time management helper library.

This module provides a small reusable utility for tracking elapsed time against
a fixed timeout. The class is intentionally minimal so it can be dropped into
contest heuristics such as beam search, hill climbing, or simulated annealing
without extra framework code.

Examples:
    >>> tm = TimeManager(timeout_seconds=5.0, start_time=2.0, clock=lambda: 7.0)
    >>> tm.elapsed()
    5.0
    >>> tm.remaining()
    0.0
    >>> tm.is_timeout()
    True
"""

from __future__ import annotations

import time
from collections.abc import Callable
from math import inf, isfinite, isnan


class TimeManager:
    """
    Track elapsed time against a fixed timeout.

    Attributes:
        timeout_seconds (float): Maximum allowed elapsed time in seconds.
        start_time (float): Reference point used by ``elapsed()``.
        clock (Callable[[], float]): Monotonic clock function returning the
            current time in seconds.

    Space Complexity:
        - ``O(1)``

    Examples:
        >>> tm = TimeManager(timeout_seconds=3.0, start_time=1.0, clock=lambda: 2.25)
        >>> round(tm.elapsed(), 2)
        1.25
        >>> round(tm.remaining(), 2)
        1.75
        >>> tm.is_timeout()
        False
    """

    __slots__ = ("timeout_seconds", "start_time", "clock")

    def __init__(
        self,
        timeout_seconds: float,
        start_time: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """
        Initialize a time manager.

        Args:
            timeout_seconds: Non-negative timeout in seconds. Positive infinity
                disables the deadline.
            start_time: Reference point for ``elapsed()``. If omitted, the current
                clock value is used when the instance is created.
            clock: Monotonic clock returning finite times in seconds, in the
                same reference frame as start_time. Defaults to perf_counter.

        Returns:
            None.

        Raises:
            ValueError: If timeout_seconds is negative or NaN, or the initial
                start_time (explicit or read from clock) is non-finite.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> tm = TimeManager(timeout_seconds=3.0, start_time=1.0, clock=lambda: 2.25)
            >>> round(tm.remaining(), 2)
            1.75
        """
        if isnan(timeout_seconds) or timeout_seconds < 0.0:
            raise ValueError('timeout_seconds must be non-negative and not NaN')
        self.timeout_seconds = timeout_seconds
        self.clock = time.perf_counter if clock is None else clock
        self.start_time = self.clock() if start_time is None else start_time
        if not isfinite(self.start_time):
            raise ValueError('start_time must be finite')

    def elapsed(self) -> float:
        """
        Return the elapsed time since construction or ``start_time``.

        Returns:
            Elapsed time in seconds. An explicit future start_time gives a
            negative value until the clock reaches it.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> tm = TimeManager(timeout_seconds=3.0, start_time=1.0, clock=lambda: 2.25)
            >>> round(tm.elapsed(), 2)
            1.25
        """

        return self.clock() - self.start_time

    def remaining(self) -> float:
        """
        Return the non-negative amount of time still available.

        Returns:
            Remaining time in seconds, clamped below by ``0.0``.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> tm = TimeManager(timeout_seconds=3.0, start_time=1.0, clock=lambda: 2.25)
            >>> round(tm.remaining(), 2)
            1.75
        """

        if self.timeout_seconds == inf:
            return inf
        return max(0.0, self.timeout_seconds - self.elapsed())

    def is_timeout(self) -> bool:
        """
        Return whether the timeout has already been reached.

        Returns:
            ``True`` if the elapsed time is at least ``timeout_seconds``,
            otherwise ``False``.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> tm = TimeManager(timeout_seconds=3.0, start_time=1.0, clock=lambda: 4.25)
            >>> tm.is_timeout()
            True
        """

        return self.timeout_seconds != inf and self.elapsed() >= self.timeout_seconds
