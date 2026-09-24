#!/usr/bin/env python3

from __future__ import annotations

from typing import TypeAlias

Index: TypeAlias = int
Value: TypeAlias = int

class FullyIndexableDictionary:
    """
    Bit vector packed in 32-bit blocks with rank and select support.

    The vector starts with all bits zero. Call build after setting bits before
    using rank or select; access reads the current bits without rebuilding.

    Attributes:
        size: Number of addressable bits.
        block: Number of 32-bit blocks used internally.

    Complexity Notation:
        n: Number of addressable bits.

    Examples:
        >>> fid = FullyIndexableDictionary(5)
        >>> fid.set(1)
        >>> fid.build()
        >>> fid.rank(5, 1)
        1

    Space Complexity:
        O(n)
    """
    def __init__(self, size: int) -> None:
        """
        Initialize an empty bit vector.

        Args:
            size: Number of bits.

        Returns:
            None.

        Raises:
            ValueError: If size is negative.

        Time Complexity:
            O(n)
        """
        if size < 0:
            raise ValueError('size must be nonnegative')
        self.size = size
        self.block = (size + 31) >> 5
        self._bit = [0] * (self.block + 1)
        self._sum = [0] * (self.block + 1)

    def _popcount(self, x: int) -> int:
        """Count set bits in a 32-bit integer using parallel bit arithmetic.

        Args:
            x (int): The integer to count set bits in.

        Returns:
            int: The number of set bits.
        """
        x = x - ((x >> 1) & 0x55555555)
        x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
        x = x + (x >> 4) & 0x0f0f0f0f
        x = x + (x >> 8)
        x = x + (x >> 16)
        return x & 0x0000007f

    def set(self, k: Index) -> None:
        """
        Set the bit at position ``k`` to ``1``.

        Call build after setting bits, before subsequent rank/select queries.

        Args:
            k: Bit position.

        Returns:
            None.

        Raises:
            AssertionError: If k is outside [0, size).

        Time Complexity:
            O(1)
        """
        assert 0 <= k < self.size
        self._bit[k >> 5] |= 1 << (k & 31)

    def build(self) -> None:
        """
        Build or rebuild prefix counts for rank and select queries.

        The bits are unchanged. Call this after the last set operation.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        for i in range(1, self.block + 1):
            self._sum[i] = self._sum[i - 1] + self._popcount(self._bit[i - 1])

    def access(self, k: Index) -> Value:
        """
        Return the bit at position ``k``.

        Args:
            k: Bit position.

        Returns:
            Bit value at ``k``.

        Raises:
            AssertionError: If k is outside [0, size).

        Time Complexity:
            O(1)
        """
        assert 0 <= k < self.size
        return (self._bit[k >> 5] >> (k & 31)) & 1

    def rank(self, k: Index, v: Value) -> int:
        """
        Count occurrences of ``v`` in ``[0, k)``.

        Args:
            k: Prefix end position.
            v: Bit value, either ``0`` or ``1``.

        Returns:
            Number of positions ``i < k`` with bit value ``v``.

        Raises:
            AssertionError: If k is outside [0, size] or v is not 0 or 1.

        Time Complexity:
            O(1)
        """
        assert 0 <= k <= self.size
        assert v in (0, 1)
        r = self._sum[k >> 5] + self._popcount(self._bit[k >> 5] & ((1 << (k & 31)) - 1))
        return r if v else k - r

    def select(self, k: Index, v: Value) -> int:
        """
        Return the position of the ``k``-th occurrence of ``v``.

        Args:
            k: Zero-based occurrence index.
            v: Bit value, either ``0`` or ``1``.

        Returns:
            Position of the ``k``-th occurrence of ``v``, or ``-1`` if absent
            or k is negative.

        Raises:
            AssertionError: If v is not 0 or 1.

        Time Complexity:
            O(log n)
        """
        assert v in (0, 1)
        if k < 0 or self.rank(self.size, v) <= k: return -1
        l, r = 0, self.size
        while r - l > 1:
            m = (l + r) // 2
            if self.rank(m, v) >= k + 1:
                r = m
            else:
                l = m
        return l


class WaveletMatrix:
    """
    Wavelet matrix for static integer sequences.

    Supports access, rank, select, quantile, and thresholded frequency and
    sum queries on a fixed array of nonnegative integers below 2**log.
    Query values and thresholds may lie outside that universe. Construction
    creates an empty matrix, and build replaces the current sequence. Bounds
    count integer operations and assume their cost is constant.

    Attributes:
        size: Length of the stored sequence.
        log: Number of processed bit levels.

    Complexity Notation:
        n: Length of the stored sequence.
        V: Size of the value universe, 2**log. In bounds below, log V means
            max(1, self.log), including the zero-bit universe.

    Space Complexity:
        O(n log V)
    """
    def __init__(self, log: int = 32) -> None:
        """
        Initialize an empty wavelet matrix.

        Args:
            log: Nonnegative bit width. Values must lie in [0, 2**log);
                log=0 permits only zero.

        Returns:
            None.

        Raises:
            ValueError: If log is negative.

        Time Complexity:
            O(log V)
        """
        if log < 0:
            raise ValueError('log must be nonnegative')
        self.size = 0
        self.log = log
        self._mat: list[FullyIndexableDictionary] = [FullyIndexableDictionary(0)] * log
        self._mid: list[int] = [0] * log
        self._cum: list[list[int]] = [[0] for _ in range(log)]
        self._prefix_sum = [0]

    def build(self, arr: list[Value]) -> None:
        """
        Build or replace the matrix from ``arr`` without changing the input.

        Args:
            arr: Integer sequence with 0 <= value < 2**log.

        Returns:
            None.

        Raises:
            ValueError: If a value lies outside [0, 2**log); the old matrix
                remains unchanged.

        Time Complexity:
            O(n log V)
        """
        limit = 1 << self.log
        if any(not 0 <= value < limit for value in arr):
            raise ValueError('values must lie in [0, 2**log)')
        self.size = len(arr)
        self._prefix_sum = [0]
        for value in arr:
            self._prefix_sum.append(self._prefix_sum[-1] + value)
        for lv in range(self.log)[::-1]:
            self._mat[lv] = FullyIndexableDictionary(self.size)
            self._cum[lv] = [0] * (self.size + 1)
            lt: list[Value] = []
            rt: list[Value] = []
            s = 0
            for i, a in enumerate(arr):
                if (a >> lv) & 1:
                    mat = self._mat[lv]
                    mat.set(i)
                    rt.append(a)
                else:
                    lt.append(a)
                    s += a
                self._cum[lv][i + 1] = s
            self._mid[lv] = len(lt)
            mat = self._mat[lv]
            mat.build()
            arr = lt + rt

    def access(self, k: Index) -> Value:
        """
        Return the value at position ``k``.

        Args:
            k: Sequence index.

        Returns:
            Stored value at ``k``.

        Raises:
            AssertionError: If k is outside [0, size).

        Time Complexity:
            O(log V)
        """
        assert 0 <= k < self.size
        res = 0
        for lv in range(self.log)[::-1]:
            mat = self._mat[lv]
            mid = self._mid[lv]
            if mat.access(k):
                res |= 1 << lv
                k = mat.rank(k, 1) + mid
            else:
                k = mat.rank(k, 0)
        return res

    def rank(self, x: Value, r: Index) -> int:
        """
        Count occurrences of ``x`` in ``[0, r)``.

        Args:
            x: Queried value.
            r: Prefix end position.

        Returns:
            Number of occurrences of ``x`` in ``[0, r)``; zero for values
            outside [0, 2**log).

        Raises:
            AssertionError: If r is outside [0, size].

        Time Complexity:
            O(log V)
        """
        assert 0 <= r <= self.size
        if not 0 <= x < 1 << self.log:
            return 0
        l = 0
        for lv in range(self.log)[::-1]:
            if (x >> lv) & 1:
                l = self._mat[lv].rank(l, 1) + self._mid[lv]
                r = self._mat[lv].rank(r, 1) + self._mid[lv]
            else:
                l = self._mat[lv].rank(l, 0)
                r = self._mat[lv].rank(r, 0)
        return r - l

    def select(self, x: Value, k: Index) -> int:
        """
        Return the position of the ``k``-th occurrence of ``x``.

        Args:
            x: Queried value.
            k: Zero-based occurrence index.

        Returns:
            Position of the ``k``-th occurrence of ``x``, or ``-1`` if absent,
            k is negative, or x lies outside [0, 2**log).

        Time Complexity:
            O(log V log n)
        """
        if k < 0 or not 0 <= x < 1 << self.log:
            return -1
        l, r = 0, self.size
        for lv in range(self.log)[::-1]:
            mat = self._mat[lv]
            if (x >> lv) & 1:
                l = mat.rank(l, 1) + self._mid[lv]
                r = mat.rank(r, 1) + self._mid[lv]
            else:
                l = mat.rank(l, 0)
                r = mat.rank(r, 0)
        if k >= r - l:
            return -1
        idx = l + k
        for lv in range(self.log):
            if (x >> lv) & 1:
                idx = self._mat[lv].select(idx - self._mid[lv], 1)
            else:
                idx = self._mat[lv].select(idx, 0)
        return idx

    def range_freq(self, l: Index, r: Index, x: Value) -> int:
        """
        Count occurrences of ``x`` in ``[l, r)``.

        Args:
            l (Index): The starting index of the subsequence.
            r (Index): The ending index of the subsequence (exclusive).
            x (Value): The value to count the frequency of.

        Returns:
            Number of occurrences of ``x`` in ``[l, r)``; zero for values
            outside [0, 2**log).

        Raises:
            AssertionError: If 0 <= l <= r <= size does not hold.

        Time Complexity:
            O(log V)
        """
        assert 0 <= l <= r <= self.size
        if not 0 <= x < 1 << self.log:
            return 0
        for lv in range(self.log)[::-1]:
            if (x >> lv) & 1:
                l = self._mat[lv].rank(l, 1) + self._mid[lv]
                r = self._mat[lv].rank(r, 1) + self._mid[lv]
            else:
                l = self._mat[lv].rank(l, 0)
                r = self._mat[lv].rank(r, 0)
        return r - l

    def range_freq_lt(self, l: Index, r: Index, x: Value) -> int:
        """
        Count values less than ``x`` in ``[l, r)``.
        Args:
            l (Index): The starting index of the subsequence.
            r (Index): The ending index of the subsequence (exclusive).
            x: Exclusive value threshold; any integer is allowed, including
                values outside the stored universe.

        Returns:
            Number of values less than ``x`` in ``[l, r)``.

        Raises:
            AssertionError: If 0 <= l <= r <= size does not hold.

        Time Complexity:
            O(log V)
        """
        assert 0 <= l <= r <= self.size
        if x <= 0:
            return 0
        if x >= 1 << self.log:
            return r - l
        res = 0
        for lv in range(self.log)[::-1]:
            if (x >> lv) & 1:
                res += self._mat[lv].rank(r, 0) - self._mat[lv].rank(l, 0)
                l += self._mid[lv] - self._mat[lv].rank(l, 0)
                r += self._mid[lv] - self._mat[lv].rank(r, 0)
            else:
                l = self._mat[lv].rank(l, 0)
                r = self._mat[lv].rank(r, 0)
        return res

    def range_sum_lt(self, l: Index, r: Index, x: Value) -> Value:
        """
        Return the sum of values less than ``x`` in ``[l, r)``.

        Args:
            l (Index): The starting index of the subsequence.
            r (Index): The ending index of the subsequence (exclusive).
            x: Exclusive value threshold; any integer is allowed, including
                values outside the stored universe.

        Returns:
            Sum of values less than ``x`` in ``[l, r)``.

        Raises:
            AssertionError: If 0 <= l <= r <= size does not hold.

        Time Complexity:
            O(log V)
        """
        assert 0 <= l <= r <= self.size
        if x <= 0:
            return 0
        if x >= 1 << self.log:
            return self._prefix_sum[r] - self._prefix_sum[l]
        res = 0
        for lv in range(self.log)[::-1]:
            if (x >> lv) & 1:
                res += self._cum[lv][r] - self._cum[lv][l]
                l += self._mid[lv] - self._mat[lv].rank(l, 0)
                r += self._mid[lv] - self._mat[lv].rank(r, 0)
            else:
                l = self._mat[lv].rank(l, 0)
                r = self._mat[lv].rank(r, 0)
        return res

    def quantile(self, l: Index, r: Index, k: Index) -> Value:
        """
        Return the ``k``-th smallest value in ``[l, r)``.

        Args:
            l (Index): The starting index of the subsequence.
            r (Index): The ending index of the subsequence (exclusive).
            k: Zero-based order statistic.

        Returns:
            The ``k``-th smallest value in ``[l, r)``.

        Raises:
            AssertionError: If 0 <= l <= r <= size does not hold
                or k is outside [0, r-l).

        Time Complexity:
            O(log V)
        """
        assert 0 <= l <= r <= self.size
        assert 0 <= k < r - l
        res = 0
        for lv in range(self.log)[::-1]:
            cnt = self._mat[lv].rank(r, 0) - self._mat[lv].rank(l, 0)
            if k >= cnt:
                res |= 1 << lv
                k -= cnt
                l = self._mat[lv].rank(l, 1) + self._mid[lv]
                r = self._mat[lv].rank(r, 1) + self._mid[lv]
            else:
                l = self._mat[lv].rank(l, 0)
                r = self._mat[lv].rank(r, 0)
        return res
