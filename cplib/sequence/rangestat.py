#!/usr/bin/env python3

from __future__ import annotations

import bisect
import math
from collections import defaultdict
from collections.abc import Callable, Sequence

from cplib.datastructure.fenwicktree import FenwickTree
from cplib.datastructure.wavelet import WaveletMatrix


_NONE = -1


class StaticRangeOrderQuery:
    """
    Static order-statistics queries on a non-negative integer array.

    The structure is a thin range-query wrapper around :class:`WaveletMatrix`.
    It supports frequency, rank/count, quantile, and thresholded sum queries.

    Args:
        arr: Input array of non-negative integers.
        log: Optional number of value bits. If omitted, it is inferred from
            the maximum value in ``arr``.

    Space Complexity:
        O(n log V)
    """

    def __init__(self, arr: Sequence[int], log: int | None = None) -> None:
        """
        Initialize the static range order query structure.

        Args:
            arr: Input array of non-negative integers.
            log: Optional number of value bits.

        Returns:
            None.

        Raises:
            ValueError: If a value is negative or does not fit in ``log`` bits.

        Time Complexity:
            O(n log V)
        """
        self.arr = list(arr)
        self.n = len(self.arr)
        if log is None:
            max_value = max(self.arr, default=0)
            log = max(1, max_value.bit_length())
        if log <= 0:
            raise ValueError('log must be positive')
        self.log = log
        self.universe = 1 << log
        for value in self.arr:
            if not 0 <= value < self.universe:
                raise ValueError('all values must satisfy 0 <= value < 2**log')

        self.prefix_sum = [0] * (self.n + 1)
        for i, value in enumerate(self.arr):
            self.prefix_sum[i + 1] = self.prefix_sum[i] + value

        self.wm = WaveletMatrix(log)
        self.wm.build(self.arr)

    def _validate_range(self, l: int, r: int) -> None:
        if not 0 <= l <= r <= self.n:
            raise ValueError('query interval must satisfy 0 <= l <= r <= n')

    def range_sum(self, l: int, r: int) -> int:
        """
        Return the sum of ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.

        Returns:
            Sum of values in ``arr[l:r]``.

        Time Complexity:
            O(1)
        """
        self._validate_range(l, r)
        return self.prefix_sum[r] - self.prefix_sum[l]

    def freq(self, l: int, r: int, x: int) -> int:
        """
        Count occurrences of ``x`` in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            x: Queried value.

        Returns:
            Number of occurrences of ``x`` in ``arr[l:r]``.

        Time Complexity:
            O(log V)
        """
        self._validate_range(l, r)
        if not 0 <= x < self.universe:
            return 0
        return self.wm.range_freq(l, r, x)

    def count_lt(self, l: int, r: int, x: int) -> int:
        """
        Count values less than ``x`` in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            x: Exclusive upper bound.

        Returns:
            Number of values ``< x`` in ``arr[l:r]``.

        Time Complexity:
            O(log V)
        """
        self._validate_range(l, r)
        if x <= 0:
            return 0
        if x >= self.universe:
            return r - l
        return self.wm.range_freq_lt(l, r, x)

    def count_le(self, l: int, r: int, x: int) -> int:
        """
        Count values at most ``x`` in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            x: Inclusive upper bound.

        Returns:
            Number of values ``<= x`` in ``arr[l:r]``.

        Time Complexity:
            O(log V)
        """
        return self.count_lt(l, r, x + 1)

    def count_between(self, l: int, r: int, lower: int, upper: int) -> int:
        """
        Count values in ``[lower, upper)`` in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            lower: Inclusive lower bound.
            upper: Exclusive upper bound.

        Returns:
            Number of values ``x`` satisfying ``lower <= x < upper``.

        Time Complexity:
            O(log V)
        """
        if lower >= upper:
            self._validate_range(l, r)
            return 0
        return self.count_lt(l, r, upper) - self.count_lt(l, r, lower)

    def sum_lt(self, l: int, r: int, x: int) -> int:
        """
        Return the sum of values less than ``x`` in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            x: Exclusive upper bound.

        Returns:
            Sum of values ``< x`` in ``arr[l:r]``.

        Time Complexity:
            O(log V)
        """
        self._validate_range(l, r)
        if x <= 0:
            return 0
        if x >= self.universe:
            return self.range_sum(l, r)
        return self.wm.range_sum_lt(l, r, x)

    def sum_le(self, l: int, r: int, x: int) -> int:
        """
        Return the sum of values at most ``x`` in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            x: Inclusive upper bound.

        Returns:
            Sum of values ``<= x`` in ``arr[l:r]``.

        Time Complexity:
            O(log V)
        """
        return self.sum_lt(l, r, x + 1)

    def sum_between(self, l: int, r: int, lower: int, upper: int) -> int:
        """
        Return the sum of values in ``[lower, upper)`` in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            lower: Inclusive lower bound.
            upper: Exclusive upper bound.

        Returns:
            Sum of values ``x`` satisfying ``lower <= x < upper``.

        Time Complexity:
            O(log V)
        """
        if lower >= upper:
            self._validate_range(l, r)
            return 0
        return self.sum_lt(l, r, upper) - self.sum_lt(l, r, lower)

    def kth_smallest(self, l: int, r: int, k: int) -> int:
        """
        Return the ``k``-th smallest value in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            k: Zero-based order index.

        Returns:
            The ``k``-th smallest value in ``arr[l:r]``.

        Raises:
            ValueError: If ``k`` is outside ``[0, r - l)``.

        Time Complexity:
            O(log V)
        """
        self._validate_range(l, r)
        if not 0 <= k < r - l:
            raise ValueError('k must satisfy 0 <= k < r - l')
        return self.wm.quantile(l, r, k)

    def quantile(self, l: int, r: int, k: int) -> int:
        """
        Return the ``k``-th smallest value in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            k: Zero-based order index.

        Returns:
            The ``k``-th smallest value in ``arr[l:r]``.

        Time Complexity:
            O(log V)
        """
        return self.kth_smallest(l, r, k)


class StaticRangeCountDistinctQuery:
    """
    Static range distinct-count queries.

    For each position, the previous occurrence index of the same value is
    stored in a wavelet matrix. The number of distinct values in ``arr[l:r]``
    is the number of positions ``i`` in ``[l, r)`` whose previous occurrence
    is smaller than ``l``.

    Args:
        arr: Input array.

    Space Complexity:
        O(n log n)
    """

    def __init__(self, arr: Sequence[int]) -> None:
        """
        Initialize the static range distinct-count structure.

        Args:
            arr: Input array.

        Returns:
            None.

        Time Complexity:
            O(n log n)
        """
        self.arr = list(arr)
        self.n = len(self.arr)
        last: dict[int, int] = {}
        previous = [0] * self.n
        for i, value in enumerate(self.arr):
            previous[i] = last.get(value, -1) + 1
            last[value] = i

        self.wm = WaveletMatrix(max(1, (self.n + 1).bit_length()))
        self.wm.build(previous)

    def count_distinct(self, l: int, r: int) -> int:
        """
        Return the number of distinct values in ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.

        Returns:
            Number of distinct values in ``arr[l:r]``.

        Raises:
            ValueError: If the query interval is outside ``[0, n]`` or ``l > r``.

        Time Complexity:
            O(log n)
        """
        if not 0 <= l <= r <= self.n:
            raise ValueError('query interval must satisfy 0 <= l <= r <= n')
        return self.wm.range_freq_lt(l, r, l + 1)

def static_range_count_distinct(arr: Sequence[int], queries: Sequence[tuple[int, int]]) -> list[int]:
    """
    Answer static range distinct-count queries.

    Args:
        arr: Input array.
        queries: Query intervals ``(l, r)`` representing ``arr[l:r]``.

    Returns:
        Distinct counts in the same order as ``queries``.

    Time Complexity:
        O(n log n + q log n)

    Space Complexity:
        O(n log n + q)
    """
    solver = StaticRangeCountDistinctQuery(arr)
    return [solver.count_distinct(l, r) for l, r in queries]


class StaticRangeMajorityQuery:
    """
    Static range strict-majority queries.

    A strict majority is a value whose frequency is more than half of the
    queried interval length. The structure first obtains a Boyer-Moore
    candidate from a segment tree, then verifies the candidate frequency using
    occurrence positions.

    Args:
        arr: Input array.

    Space Complexity:
        O(n)
    """

    def __init__(self, arr: Sequence[int]) -> None:
        """
        Initialize the static range majority structure.

        Args:
            arr: Input array.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.arr = list(arr)
        self.n = len(self.arr)
        self.positions: defaultdict[int, list[int]] = defaultdict(list)
        for i, value in enumerate(self.arr):
            self.positions[value].append(i)

        self.size = 1 << (self.n - 1).bit_length() if self.n else 1
        self.data = [(0, 0)] * (2 * self.size)
        for i, value in enumerate(self.arr):
            self.data[self.size + i] = (value, 1)
        for i in range(self.size - 1, 0, -1):
            self.data[i] = self._op(self.data[2 * i], self.data[2 * i + 1])

    @staticmethod
    def _op(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
        value1, count1 = left
        value2, count2 = right
        if count1 == 0:
            return right
        if count2 == 0:
            return left
        if value1 == value2:
            return (value1, count1 + count2)
        if count1 > count2:
            return (value1, count1 - count2)
        return (value2, count2 - count1)

    def _candidate(self, l: int, r: int) -> int:
        sml = (0, 0)
        smr = (0, 0)
        l += self.size
        r += self.size
        while l < r:
            if l & 1:
                sml = self._op(sml, self.data[l])
                l += 1
            if r & 1:
                r -= 1
                smr = self._op(self.data[r], smr)
            l >>= 1
            r >>= 1
        return self._op(sml, smr)[0]

    def range_majority(self, l: int, r: int) -> int | None:
        """
        Return the strict majority value of ``arr[l:r]`` if it exists.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.

        Returns:
            The strict majority value, or ``None`` if it does not exist.

        Raises:
            ValueError: If the interval is empty or outside ``[0, n]``.

        Time Complexity:
            O(log n)
        """
        if not 0 <= l < r <= self.n:
            raise ValueError('query interval must satisfy 0 <= l < r <= n')
        candidate = self._candidate(l, r)
        positions = self.positions[candidate]
        count = bisect.bisect_left(positions, r) - bisect.bisect_left(positions, l)
        return candidate if count > (r - l) // 2 else None

    def majority_or(self, l: int, r: int, default: int = -1) -> int:
        """
        Return the strict majority value of ``arr[l:r]`` or ``default``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.
            default: Value returned when no strict majority exists.

        Returns:
            The strict majority value, or ``default``.

        Time Complexity:
            O(log n)
        """
        value = self.range_majority(l, r)
        return default if value is None else value

class StaticRangeModeQuery:
    """
    Static range mode query with sqrt decomposition.

    The array is immutable after construction. Each query returns the value
    with maximum frequency in a half-open interval ``[l, r)`` together with
    its frequency.

    Args:
        n: Length of the array.
        arr: Initial array of length ``n``.

    Space Complexity:
        O(n + num_blocks^2)

    Examples:
        >>> rmq = StaticRangeModeQuery(5, [1, 2, 2, 3, 2])
        >>> rmq.range_mode(1, 5)
        (2, 3)
    """

    def __init__(self, n: int, arr: Sequence[int]) -> None:
        """
        Initialize the structure from an immutable array.

        Args:
            n: Array length.
            arr: Initial array.

        Returns:
            None.

        Raises:
            ValueError: If ``len(arr) != n``.

        Time Complexity:
            O(num_blocks^2 * B), where ``B`` is the block size
        """
        self.n = n
        if len(arr) != n:
            raise ValueError('Length of arr must be equal to n.')
        self.arr = list(arr)

        block_size_limit = 150
        self.B = max(min(block_size_limit, math.isqrt(n)), 1)
        self.num_blocks = (self.n + self.B - 1) // self.B

        self.pos_lists: defaultdict[int, list[int]] = defaultdict(list)
        for idx, value in enumerate(self.arr):
            self.pos_lists[value].append(idx)

        self.block_mode = [[(-1, 0) for _ in range(self.num_blocks)] for _ in range(self.num_blocks)]
        for left_block in range(self.num_blocks):
            freq: dict[int, int] = {}
            current_mode = -1
            current_count = 0
            for right_block in range(left_block, self.num_blocks):
                start = right_block * self.B
                end = min((right_block + 1) * self.B, self.n)
                for index in range(start, end):
                    value = self.arr[index]
                    freq[value] = freq.get(value, 0) + 1
                    if freq[value] > current_count:
                        current_count = freq[value]
                        current_mode = value
                self.block_mode[left_block][right_block] = (current_mode, current_count)

    def range_mode(self, l: int, r: int) -> tuple[int, int]:
        """
        Return the mode of ``arr[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.

        Returns:
            A pair ``(value, count)`` where ``value`` is a mode of the range
            and ``count`` is its frequency. Ties may be resolved arbitrarily.

        Raises:
            ValueError: If the interval is empty or outside ``[0, n]``.

        Time Complexity:
            O(B log n) in the worst case, where ``B`` is the block size
        """
        if not 0 <= l < r <= self.n:
            raise ValueError('query interval must satisfy 0 <= l < r <= n')

        left_block = l // self.B
        right_block = (r - 1) // self.B

        if left_block == right_block:
            freq: dict[int, int] = {}
            mode_value = -1
            mode_count = 0
            for index in range(l, r):
                value = self.arr[index]
                freq[value] = freq.get(value, 0) + 1
                if freq[value] > mode_count:
                    mode_count = freq[value]
                    mode_value = value
            return (mode_value, mode_count)

        mode_value = -1
        mode_count = 0
        if left_block + 1 <= right_block - 1:
            mode_value, mode_count = self.block_mode[left_block + 1][right_block - 1]

        checked: set[int] = set()

        left_end = (left_block + 1) * self.B
        for index in range(l, left_end):
            value = self.arr[index]
            if value in checked:
                continue
            checked.add(value)
            positions = self.pos_lists[value]
            if len(positions) <= mode_count:
                continue
            count = bisect.bisect_left(positions, r) - bisect.bisect_left(positions, l)
            if count > mode_count:
                mode_count = count
                mode_value = value

        right_start = right_block * self.B
        for index in range(right_start, r):
            value = self.arr[index]
            if value in checked:
                continue
            checked.add(value)
            positions = self.pos_lists[value]
            if len(positions) <= mode_count:
                continue
            count = bisect.bisect_left(positions, r) - bisect.bisect_left(positions, l)
            if count > mode_count:
                mode_count = count
                mode_value = value

        return (mode_value, mode_count)


class StaticRangeLISQuery:
    """
    Static range LIS queries on a permutation.

    The input must be a permutation of ``0, 1, ..., n - 1``. The structure
    builds the seaweed representation for semi-local LIS and stores it in a
    wavelet matrix.

    Args:
        p: Input permutation.

    Space Complexity:
        O(n log n)
    """

    def __init__(self, p: Sequence[int]) -> None:
        """
        Initialize the static range LIS structure.

        Args:
            p: Input permutation of ``0, 1, ..., n - 1``.

        Returns:
            None.

        Raises:
            ValueError: If ``p`` is not a permutation.

        Time Complexity:
            O(n log^2 n)
        """
        self.n = len(p)
        self.p = list(p)
        if not _is_permutation(self.p):
            raise ValueError('p must be a permutation of 0, 1, ..., n - 1')

        row = _seaweed_doubling(self.p) if self.n else []
        row = [self.n if x == _NONE else x for x in row]
        self.wm = WaveletMatrix(max(1, self.n.bit_length()))
        self.wm.build(row)

    def range_lis(self, l: int, r: int) -> int:
        """
        Return the LIS length of ``p[l:r]``.

        Args:
            l: Left endpoint of the query interval, inclusive.
            r: Right endpoint of the query interval, exclusive.

        Returns:
            Length of the longest increasing subsequence in ``p[l:r]``.

        Raises:
            ValueError: If the query interval is outside ``[0, n]`` or ``l > r``.

        Time Complexity:
            O(log n)
        """
        if not 0 <= l <= r <= self.n:
            raise ValueError('query interval must satisfy 0 <= l <= r <= n')
        return (r - l) - self.wm.range_freq_lt(l, self.n, r)

def static_range_lis(p: Sequence[int], queries: Sequence[tuple[int, int]]) -> list[int]:
    """
    Answer static range LIS queries on a permutation.

    Args:
        p: Input permutation of ``0, 1, ..., n - 1``.
        queries: Query intervals ``(l, r)`` representing ``p[l:r]``.

    Returns:
        LIS lengths in the same order as ``queries``.

    Time Complexity:
        O(n log^2 n + q log n)

    Space Complexity:
        O(n log n + q)
    """
    solver = StaticRangeLISQuery(p)
    return [solver.range_lis(l, r) for l, r in queries]


class OfflineStaticRangeInversionsQuery:
    """
    Offline static range inversion-count queries.

    All queries are answered with Mo's algorithm and a Fenwick tree over
    coordinate-compressed values.

    Args:
        arr: Input array.
        block_size: Optional block size passed to :class:`Mo`.

    Space Complexity:
        O(n + q)
    """

    def __init__(self, arr: Sequence[int], block_size: int | None = None) -> None:
        """
        Initialize the offline static range inversion solver.

        Args:
            arr: Input array.
            block_size: Optional Mo block size.

        Returns:
            None.

        Time Complexity:
            O(n log n)
        """
        self.arr = list(arr)
        self.n = len(self.arr)
        values = sorted(set(self.arr))
        comp = {value: i for i, value in enumerate(values)}
        self.compressed = [comp[value] for value in self.arr]
        self.value_count = len(values)
        self.block_size = block_size

    def solve(self, queries: Sequence[tuple[int, int]]) -> list[int]:
        """
        Answer inversion-count queries for half-open intervals.

        Args:
            queries: Query intervals ``(l, r)`` representing ``arr[l:r]``.

        Returns:
            Inversion counts in the same order as ``queries``.

        Raises:
            ValueError: If a query interval is outside ``[0, n]`` or ``l > r``.

        Time Complexity:
            O((n + q) sqrt(n) log n) with the standard Mo ordering

        Space Complexity:
            O(n + q)
        """
        from cplib.algorithm.mo import Mo

        mo = Mo[int](self.n, block_size=self.block_size)
        for l, r in queries:
            mo.add_query(l, r)

        fenwick = FenwickTree(max(1, self.value_count))
        active_count = 0
        inversions = 0

        def add_left(index: int) -> None:
            nonlocal active_count, inversions
            value = self.compressed[index]
            inversions += fenwick.sum(value)
            active_count += 1
            fenwick.add(value, 1)

        def add_right(index: int) -> None:
            nonlocal active_count, inversions
            value = self.compressed[index]
            inversions += active_count - fenwick.sum(value + 1)
            active_count += 1
            fenwick.add(value, 1)

        def remove_left(index: int) -> None:
            nonlocal active_count, inversions
            value = self.compressed[index]
            inversions -= fenwick.sum(value)
            active_count -= 1
            fenwick.add(value, -1)

        def remove_right(index: int) -> None:
            nonlocal active_count, inversions
            value = self.compressed[index]
            inversions -= active_count - fenwick.sum(value + 1)
            active_count -= 1
            fenwick.add(value, -1)

        return mo.run(add_left, add_right, remove_left, remove_right, lambda _: inversions)


def offline_static_range_inversions(arr: Sequence[int], queries: Sequence[tuple[int, int]]) -> list[int]:
    """
    Answer static range inversion-count queries offline.

    Args:
        arr: Input array.
        queries: Query intervals ``(l, r)`` representing ``arr[l:r]``.

    Returns:
        Inversion counts in the same order as ``queries``.

    Time Complexity:
        O((n + q) sqrt(n) log n) with the standard Mo ordering

    Space Complexity:
        O(n + q)
    """
    return OfflineStaticRangeInversionsQuery(arr).solve(queries)


class OfflineStaticRangeMexQuery:
    """
    Offline static range mex queries on an immutable integer array.

    All queries are answered offline. For each right endpoint, the structure
    keeps the latest occurrence of every value in ``[0, n]``. The mex of
    ``arr[l:r]`` is the smallest value whose latest occurrence is smaller than
    ``l``.

    Args:
        n: Length of the array.
        arr: Initial array of length ``n``.

    Space Complexity:
        O(n + q)
    """

    def __init__(self, n: int, arr: Sequence[int]) -> None:
        """
        Initialize the offline static range mex solver.

        Args:
            n: Array length.
            arr: Initial array.

        Returns:
            None.

        Raises:
            ValueError: If ``len(arr) != n``.

        Time Complexity:
            O(n)
        """
        if len(arr) != n:
            raise ValueError('Length of arr must be equal to n.')
        self.n = n
        self.arr = list(arr)

    def solve(self, queries: Sequence[tuple[int, int]]) -> list[int]:
        """
        Answer mex queries for half-open intervals.

        Args:
            queries: Query intervals ``(l, r)`` representing ``arr[l:r]``.

        Returns:
            Mex values in the same order as ``queries``.

        Raises:
            ValueError: If a query interval is outside ``[0, n]`` or ``l > r``.

        Time Complexity:
            O((n + q) log n)

        Space Complexity:
            O(n + q)
        """
        buckets: list[list[tuple[int, int]]] = [[] for _ in range(self.n + 1)]
        for i, (l, r) in enumerate(queries):
            if not 0 <= l <= r <= self.n:
                raise ValueError('query interval must satisfy 0 <= l <= r <= n')
            buckets[r].append((i, l))

        tree = _RangeMinPointSet(self.n + 1, -1, self.n + 1)
        answers = [0] * len(queries)

        for i, l in buckets[0]:
            answers[i] = tree.first_less_than(l)
        for r, value in enumerate(self.arr, 1):
            if 0 <= value <= self.n:
                tree.set(value, r - 1)
            for i, l in buckets[r]:
                answers[i] = tree.first_less_than(l)
        return answers


def offline_static_range_mex(arr: Sequence[int], queries: Sequence[tuple[int, int]]) -> list[int]:
    """
    Answer static range mex queries offline on an immutable integer array.

    Args:
        arr: Input array.
        queries: Query intervals ``(l, r)`` representing ``arr[l:r]``.

    Returns:
        Mex values in the same order as ``queries``.

    Time Complexity:
        O((n + q) log n)

    Space Complexity:
        O(n + q)
    """
    return OfflineStaticRangeMexQuery(len(arr), arr).solve(queries)


class _RangeMinPointSet:
    """Minimum tree for offline mex queries, avoiding predicate callbacks."""

    def __init__(self, n: int, initial: int, inf: int) -> None:
        self.n = n
        self.size = 1 << (n - 1).bit_length()
        self.inf = inf
        self.data = [inf] * (2 * self.size)
        for i in range(n):
            self.data[self.size + i] = initial
        for i in range(self.size - 1, 0, -1):
            self.data[i] = min(self.data[2 * i], self.data[2 * i + 1])

    def set(self, p: int, value: int) -> None:
        p += self.size
        self.data[p] = value
        p >>= 1
        while p:
            self.data[p] = min(self.data[2 * p], self.data[2 * p + 1])
            p >>= 1

    def first_less_than(self, threshold: int) -> int:
        if self.data[1] >= threshold:
            return self.n
        k = 1
        while k < self.size:
            if self.data[2 * k] < threshold:
                k = 2 * k
            else:
                k = 2 * k + 1
        return k - self.size


def _is_permutation(p: Sequence[int]) -> bool:
    n = len(p)
    used = [False] * n
    for x in p:
        if not 0 <= x < n or used[x]:
            return False
        used[x] = True
    return True


def _inverse_permutation_with_none(p: Sequence[int]) -> list[int]:
    q = [_NONE] * len(p)
    for i, x in enumerate(p):
        if x != _NONE:
            q[x] = i
    return q


def _unit_monge_dmul(a: Sequence[int], b: Sequence[int]) -> list[int]:
    n = len(a)
    if n == 1:
        return [0]

    c_row = [0] * n
    c_col = [0] * n
    mid = n // 2

    def map_half(length: int, is_in_half: Callable[[int], bool], shift: Callable[[int], int]) -> None:
        a_half: list[int] = []
        b_half: list[int] = []
        a_map: list[int] = []
        b_map: list[int] = []
        for i in range(n):
            if is_in_half(a[i]):
                a_half.append(shift(a[i]))
                a_map.append(i)
            if is_in_half(b[i]):
                b_half.append(shift(b[i]))
                b_map.append(i)

        c_half = _unit_monge_dmul(a_half, b_half)
        for i in range(length):
            row = a_map[i]
            col = b_map[c_half[i]]
            c_row[row] = col
            c_col[col] = row

    def is_in_lower_half(x: int) -> bool:
        return x < mid

    def lower_half_shift(x: int) -> int:
        return x

    def is_in_upper_half(x: int) -> bool:
        return x >= mid

    def upper_half_shift(x: int) -> int:
        return x - mid

    map_half(mid, is_in_lower_half, lower_half_shift)
    map_half(n - mid, is_in_upper_half, upper_half_shift)

    neg_delta = 0
    neg_col = 0
    pos_delta = 0
    pos_col = 0
    row = n

    def right(delta: int, col: int) -> tuple[int, int]:
        if b[col] < mid:
            if c_col[col] >= row:
                delta += 1
        else:
            if c_col[col] < row:
                delta += 1
        return delta, col + 1

    def up(delta: int, col: int) -> int:
        if a[row] < mid:
            if c_row[row] >= col:
                delta -= 1
        else:
            if c_row[row] < col:
                delta -= 1
        return delta

    while row:
        while pos_col != n:
            next_delta, next_col = right(pos_delta, pos_col)
            if next_delta != 0:
                break
            pos_delta, pos_col = next_delta, next_col
        row -= 1
        neg_delta = up(neg_delta, neg_col)
        pos_delta = up(pos_delta, pos_col)
        while neg_delta != 0:
            neg_delta, neg_col = right(neg_delta, neg_col)
        if neg_col > pos_col:
            c_row[row] = pos_col

    return c_row


def _subunit_monge_dmul(a: list[int], b: list[int]) -> list[int]:
    n = len(a)
    a_inv = _inverse_permutation_with_none(a)
    b_inv = _inverse_permutation_with_none(b)
    b, b_inv = b_inv, b

    a_map: list[int] = []
    for i in range(n - 1, -1, -1):
        if a[i] != _NONE:
            a_map.append(i)
            a[n - len(a_map)] = a[i]
    a_map.reverse()

    cnt = 0
    for i in range(n):
        if a_inv[i] == _NONE:
            a[cnt] = i
            cnt += 1

    b_map: list[int] = []
    for i in range(n):
        if b[i] != _NONE:
            b[len(b_map)] = b[i]
            b_map.append(i)

    cnt = len(b_map)
    for i in range(n):
        if b_inv[i] == _NONE:
            b[cnt] = i
            cnt += 1

    c = _unit_monge_dmul(a, b)
    result = [_NONE] * n
    offset = n - len(a_map)
    for i, row in enumerate(a_map):
        t = c[offset + i]
        if t < len(b_map):
            result[row] = b_map[t]
    return result


def _seaweed_doubling(p: Sequence[int]) -> list[int]:
    n = len(p)
    if n == 1:
        return [_NONE]

    mid = n // 2
    lo: list[int] = []
    hi: list[int] = []
    lo_map: list[int] = []
    hi_map: list[int] = []
    for i, x in enumerate(p):
        if x < mid:
            lo.append(x)
            lo_map.append(i)
        else:
            hi.append(x - mid)
            hi_map.append(i)

    lo = _seaweed_doubling(lo)
    hi = _seaweed_doubling(hi)

    lo_pad = list(range(n))
    hi_pad = list(range(n))
    for i in range(mid):
        if lo[i] == _NONE:
            lo_pad[lo_map[i]] = _NONE
        else:
            lo_pad[lo_map[i]] = lo_map[lo[i]]
    for i in range(n - mid):
        if hi[i] == _NONE:
            hi_pad[hi_map[i]] = _NONE
        else:
            hi_pad[hi_map[i]] = hi_map[hi[i]]

    return _subunit_monge_dmul(lo_pad, hi_pad)
