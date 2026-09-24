#!/usr/bin/env python3

from typing import Generic
from collections.abc import Callable
from cplib.tools.type import ValueT


class SlidingWindowAggregation(Generic[ValueT]):
    """
    Double-ended sliding-window aggregation structure.

    Supports efficient aggregation queries over a sliding window.
    Maintains a deque-like structure that allows push and pop from both ends
    while supporting constant-time aggregation over the whole window.

    Examples:
        >>> swag = SlidingWindowAggregation[int](lambda a, b: a + b)
        >>> swag.push_back(1)
        >>> swag.push_back(2)
        >>> swag.push_back(3)
        >>> swag.all_prod()
        6
        >>> swag.pop_front()
        >>> swag.all_prod()
        5

    Space Complexity:
        O(n)
    """
    def __init__(self, op: Callable[[ValueT, ValueT], ValueT]) -> None:
        """
        Initialize an empty sliding window.

        Args:
            op: Associative aggregation operation, not necessarily commutative.
                Complexity bounds assume O(1) calls and fixed-size values.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.lval: list[ValueT] = []
        self.rval: list[ValueT] = []
        self.lsum: list[ValueT] = []
        self.rsum: list[ValueT] = []
        self.op = op

    def is_empty(self) -> bool:
        """
        Check if the window is empty.

        Returns:
            ``True`` if the window is empty, otherwise ``False``.

        Time Complexity:
            O(1)
        """
        return not (len(self.lsum) or len(self.rsum))

    def push_front(self, x: ValueT) -> None:
        """
        Push element to the front of the window.

        Args:
            x: Element to push.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        if not self.lsum:
            self.lval.append(x)
            self.lsum.append(x)
        else:
            self.lval.append(x)
            self.lsum.append(self.op(x, self.lsum[-1]))

    def push_back(self, x: ValueT) -> None:
        """
        Push element to the back of the window.

        Args:
            x: Element to push.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        if not self.rsum:
            self.rval.append(x)
            self.rsum.append(x)
        else:
            self.rval.append(x)
            self.rsum.append(self.op(self.rsum[-1], x))

    def pop_front(self) -> None:
        """
        Pop element from the front of the window.

        Returns:
            None.

        Raises:
            IndexError: If the window is empty.

        Time Complexity:
            Amortized O(1)
        """
        if not self.lsum:
            rn = len(self.rsum) // 2
            ln = len(self.rsum) - rn
            rv: list[ValueT] = []
            self.rsum.clear()
            for _ in range(rn):
                rv.append(self.rval.pop())
            for _ in range(ln):
                x = self.rval.pop()
                self.lval.append(x)
                if not self.lsum:
                    self.lsum.append(x)
                else:
                    self.lsum.append(self.op(x, self.lsum[-1]))
            for _ in range(rn):
                x = rv.pop()
                self.rval.append(x)
                if not self.rsum:
                    self.rsum.append(x)
                else:
                    self.rsum.append(self.op(self.rsum[-1], x))
        self.lval.pop()
        self.lsum.pop()

    def pop_back(self) -> None:
        """
        Pop element from the back of the window.

        Returns:
            None.

        Raises:
            IndexError: If the window is empty.

        Time Complexity:
            Amortized O(1)
        """
        if not self.rsum:
            ln = len(self.lsum) // 2
            rn = len(self.lsum) - ln
            lv: list[ValueT] = []
            self.lsum.clear()
            for _ in range(ln):
                lv.append(self.lval.pop())
            for _ in range(rn):
                x = self.lval.pop()
                self.rval.append(x)
                if not self.rsum:
                    self.rsum.append(x)
                else:
                    self.rsum.append(self.op(self.rsum[-1], x))
            for _ in range(ln):
                x = lv.pop()
                self.lval.append(x)
                if not self.lsum:
                    self.lsum.append(x)
                else:
                    self.lsum.append(self.op(x, self.lsum[-1]))
        self.rval.pop()
        self.rsum.pop()

    def all_prod(self) -> ValueT:
        """
        Aggregate all elements of a nonempty window from front to back.

        Returns:
            Aggregate of all elements in the window.

        Raises:
            IndexError: If the window is empty; no identity element is stored.

        Time Complexity:
            O(1)
        """
        if not self.rsum:
            return self.lsum[-1]
        elif not self.lsum:
            return self.rsum[-1]
        else:
            return self.op(self.lsum[-1], self.rsum[-1])
