#!/usr/bin/env python3

from typing import Generic
from collections.abc import Callable, Sequence
from bisect import bisect_right

from cplib.datastructure.persistent import FullyPersistentSegmentTree as FullyPersistentSegmentTree
from cplib.datastructure.persistent import FullyPersistentLazySegmentTree as FullyPersistentLazySegmentTree
from cplib.tools.type import KeyT, ValueT, ActionT


class SegmentTree(Generic[ValueT]):
    """Segment tree for point updates and ordered range products.

    op must be associative with two-sided identity e; it need not be commutative.
    Callbacks must not mutate their inputs. Complexity bounds assume O(1)
    callbacks and fixed-size values. Initially all n elements equal e.

    Space Complexity:
        O(n + 1).
    """

    def __init__(self, n: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT) -> None:
        """Initialize a segment tree with `n` elements.

        Args:
            n (int): Number of elements in the segment tree.
            op (Callable[[ValueT, ValueT], ValueT]): Binary operation used to combine elements. Assumed to be associative and O(1) Time Complexity.
            e (ValueT): Identity element for the binary operation `op`.

        Time Complexity:
            O(n) in the size of the processed input or stored data

        Raises:
            ValueError: If a capacity is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.op = op
        self.e = e
        self.log = max(0, n - 1).bit_length()
        self.size = 1 << self.log
        self.d = [e] * (2 * self.size)

    def _update(self, k: int) -> None:
        self.d[k] = self.op(self.d[2 * k], self.d[2 * k + 1])

    def build(self, arr: Sequence[ValueT]) -> None:
        """Build the segment tree from a sequence of elements.

        Args:
            arr (Sequence[ValueT]): At most n elements. Remaining positions are reset to e.

        Raises:
            AssertionError: If ``len(arr) <= n`` is false.

        Time Complexity:
            O(n)

        Returns:
            None.
        """
        assert len(arr) <= self.n
        self.d = [self.e] * (2 * self.size)
        for i, a in enumerate(arr):
            self.d[self.size + i] = a
        for i in range(1, self.size)[::-1]:
            self._update(i)

    def set(self, p: int, x: ValueT) -> None:
        """Set the element at position `p` to `x`.

        Args:
            p (int): Index of the element to set.
            x (ValueT): New value of the element.

        Raises:
            AssertionError: If ``0 <= p < n`` is false.

        Time Complexity:
            O(log n)

        Returns:
            None.
        """
        assert 0 <= p < self.n
        p += self.size
        self.d[p] = x
        for i in range(1, self.log + 1):
            self._update(p >> i)

    def get(self, p: int) -> ValueT:
        """
        Retrieve the element at position `p`.

        Args:
            p (int): Index of the element to retrieve.

        Returns:
            ValueT: Value of the element at position `p`.

        Raises:
            AssertionError: If ``0 <= p < n`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= p < self.n
        return self.d[p + self.size]

    def prod(self, l: int, r: int) -> ValueT:
        """
        Compute the result of applying the binary operation over the segment [l, r).

        Args:
            l (int): Left endpoint (inclusive).
            r (int): Right endpoint (exclusive).

        Returns:
            ValueT: Result of the binary operation over the segment.

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= l <= r <= self.n
        sml = smr = self.e
        l += self.size
        r += self.size
        while l < r:
            if l & 1:
                sml = self.op(sml, self.d[l])
                l += 1
            if r & 1:
                r -= 1
                smr = self.op(self.d[r], smr)
            l >>= 1
            r >>= 1
        return self.op(sml, smr)

    def all_prod(self) -> ValueT:
        """
        Compute the result of applying the binary operation over the entire segment.

        Returns:
            ValueT: Result of the binary operation over the segment.

        Time Complexity:
            O(1)
        """
        return self.d[1]

    def max_right(self, l: int, f: Callable[[ValueT], bool]) -> int:
        """Find the maximum `r` such that `f(op(a[l], a[l+1], ..., a[r-1]))` is True.

        Args:
            l (int): Left endpoint (inclusive).
            f (Callable[[ValueT], bool]): A boolean function to satisfy.

        Returns:
            int: Maximum `r`.

        Raises:
            AssertionError: If any of ``0 <= l <= n``, ``f(e)`` is false.

        Time Complexity:
            O(log n)

        Notes:
            The predicate must be deterministic, accept e, and stay False once
            it becomes False as the queried interval is extended.
        """
        assert 0 <= l <= self.n
        assert f(self.e)
        if l == self.n:
            return self.n
        l += self.size
        sm = self.e
        while True:
            while l % 2 == 0:
                l >>= 1
            if not f(self.op(sm, self.d[l])):
                while l < self.size:
                    l = 2 * l
                    if f(self.op(sm, self.d[l])):
                        sm = self.op(sm, self.d[l])
                        l += 1
                return l - self.size
            sm = self.op(sm, self.d[l])
            l += 1
            if (l & -l) == l:
                return self.n

    def min_left(self, r: int, f: Callable[[ValueT], bool]) -> int:
        """Find the minimum `l` such that `f(op(a[l], a[l+1], ..., a[r-1]))` is True.

        Args:
            r (int): Right endpoint (exclusive).
            f (Callable[[ValueT], bool]): A boolean function to satisfy.

        Returns:
            int: Minimum `l`.

        Raises:
            AssertionError: If any of ``0 <= r <= n``, ``f(e)`` is false.

        Time Complexity:
            O(log n)

        Notes:
            The predicate must be deterministic, accept e, and stay False once
            it becomes False as the queried interval is extended.
        """
        assert 0 <= r <= self.n
        assert f(self.e)
        if r == 0:
            return 0
        r += self.size
        sm = self.e
        while True:
            r -= 1
            while r > 1 and (r % 2):
                r >>= 1
            if not f(self.op(self.d[r], sm)):
                while r < self.size:
                    r = 2 * r + 1
                    if f(self.op(self.d[r], sm)):
                        sm = self.op(self.d[r], sm)
                        r -= 1
                return r + 1 - self.size
            sm = self.op(self.d[r], sm)
            if (r & -r) == r:
                return 0


class RangeMinPointSet(SegmentTree[int]):
    """Segment tree specialized for point updates and range minima.

    Args:
        n: Number of elements.
        inf: Identity for min. All stored values must be at most inf.

    Space Complexity:
        O(n + 1). See inherited methods for operation costs.
    """

    def __init__(self, n: int, inf: int = 1 << 30) -> None:
        """Initialize a segment tree for range minimum query (RMQ) with `n` elements.

        Args:
            n (int): Number of elements in the segment tree.
            inf (int, optional): A value treated as positive infinity for minimum operations. Defaults to 1 << 30.

        Time Complexity:
            O(n)

        Returns:
            None.
        """
        super().__init__(n, min, inf)


class RangeLinearAddRangeMin:
    """
    Range linear-add and range-min structure by sqrt decomposition.

    This structure maintains an integer sequence ``a`` and supports:

    - ``range_linear_add(l, r, b, c)``:
      add ``b * i + c`` to each ``a[i]`` for ``i`` in ``[l, r)``.
    - ``range_min(l, r)``:
      return ``min(a[l:r])``.

    Each block stores a lazy linear function and the lower envelope of
    ``base[i] + slope * i`` over vertices in that block. The current block
    minimum is cached, so full-block queries are constant-time after updates.

    Space Complexity:
        ``O(n)``
    """

    def __init__(self, values: Sequence[int], block_size: int | None = None) -> None:
        """Build the data structure from initial values.

        Args:
            values: Initial sequence.
            block_size: Optional sqrt-decomposition block size. If omitted, a
                value tuned for ``N, Q <= 10^5`` is used.

        Time Complexity:
            ``O(n)``

        Raises:
            ValueError: If block_size is specified and is not positive.

        Returns:
            None.
        """
        if block_size is not None and block_size <= 0:
            raise ValueError('block_size must be positive')
        self.n = len(values)
        self.values = list(values)
        self.inf = 1 << 80
        if self.n == 0:
            self.block_size = 1
            self.block_count = 0
            self.block_left: list[int] = []
            self.block_right: list[int] = []
            self.block_id: list[int] = []
            self.lazy_b: list[int] = []
            self.lazy_c: list[int] = []
            self.hull: list[list[tuple[int, int]]] = []
            self.block_min: list[int] = []
            self.dirty: list[bool] = []
            return
        self.block_size = block_size if block_size is not None else min(self.n, 700)
        self.block_count = (self.n + self.block_size - 1) // self.block_size
        self.block_left = [i * self.block_size for i in range(self.block_count)]
        self.block_right = [min(self.n, (i + 1) * self.block_size) for i in range(self.block_count)]
        self.block_id = [i // self.block_size for i in range(self.n)]
        self.lazy_b = [0] * self.block_count
        self.lazy_c = [0] * self.block_count
        self.hull: list[list[tuple[int, int]]] = [[] for _ in range(self.block_count)]
        self.block_min = [self.inf] * self.block_count
        self.dirty = [False] * self.block_count
        for block in range(self.block_count):
            self._rebuild(block)

    @staticmethod
    def _is_unnecessary(line1: tuple[int, int], line2: tuple[int, int], line3: tuple[int, int]) -> bool:
        m1, b1 = line1
        m2, b2 = line2
        m3, b3 = line3
        return (b2 - b1) * (m2 - m3) >= (b3 - b2) * (m1 - m2)

    @staticmethod
    def _eval(line: tuple[int, int], x: int) -> int:
        return line[0] * x + line[1]

    def _query_hull(self, block: int, slope: int) -> int:
        hull = self.hull[block]
        lo = 0
        hi = len(hull) - 1
        while lo < hi:
            mid = (lo + hi) >> 1
            if self._eval(hull[mid], slope) >= self._eval(hull[mid + 1], slope):
                lo = mid + 1
            else:
                hi = mid
        return self._eval(hull[lo], slope)

    def _rebuild(self, block: int) -> None:
        hull: list[tuple[int, int]] = []
        for idx in range(self.block_right[block] - 1, self.block_left[block] - 1, -1):
            line = (idx, self.values[idx])
            while len(hull) >= 2 and self._is_unnecessary(hull[-2], hull[-1], line):
                hull.pop()
            hull.append(line)
        self.hull[block] = hull
        self.block_min[block] = self._query_hull(block, self.lazy_b[block]) + self.lazy_c[block]
        self.dirty[block] = False

    def _ensure_block_min(self, block: int) -> None:
        if self.dirty[block]:
            self.block_min[block] = self._query_hull(block, self.lazy_b[block]) + self.lazy_c[block]
            self.dirty[block] = False

    def _materialize(self, block: int) -> None:
        lazy_b = self.lazy_b[block]
        lazy_c = self.lazy_c[block]
        if lazy_b == 0 and lazy_c == 0:
            return
        for idx in range(self.block_left[block], self.block_right[block]):
            self.values[idx] += lazy_b * idx + lazy_c
        self.lazy_b[block] = 0
        self.lazy_c[block] = 0

    def range_linear_add(self, l: int, r: int, b: int, c: int) -> None:
        """Add ``b * i + c`` to every ``a[i]`` for ``i`` in ``[l, r)``.

        Args:
            l: Inclusive left boundary.
            r: Exclusive right boundary.
            b: Linear coefficient.
            c: Constant coefficient.

        Time Complexity:
            ``O(B + n / B)`` worst-case, where ``B`` is the block size.

        Raises:
            AssertionError: If the position or interval is out of bounds.

        Returns:
            None.
        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return
        left_block = self.block_id[l]
        right_block = self.block_id[r - 1]
        if left_block == right_block:
            self._materialize(left_block)
            for idx in range(l, r):
                self.values[idx] += b * idx + c
            self._rebuild(left_block)
            return
        self._materialize(left_block)
        for idx in range(l, self.block_right[left_block]):
            self.values[idx] += b * idx + c
        self._rebuild(left_block)
        self._materialize(right_block)
        for idx in range(self.block_left[right_block], r):
            self.values[idx] += b * idx + c
        self._rebuild(right_block)
        for block in range(left_block + 1, right_block):
            self.lazy_b[block] += b
            self.lazy_c[block] += c
            self.dirty[block] = True

    def range_min(self, l: int, r: int) -> int:
        """Return the minimum value in ``a[l:r]``.

        Args:
            l: Inclusive left boundary.
            r: Exclusive right boundary.

        Time Complexity:
            ``O(B + (n / B) * log(B + 1))`` worst-case, where ``B`` is the block size.

        Returns:
            Minimum value, or self.inf (2**80) for an empty range. Nonempty
            results are not bounded by self.inf.

        Raises:
            AssertionError: If the position or interval is out of bounds.
        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return self.inf
        left_block = self.block_id[l]
        right_block = self.block_id[r - 1]
        res = self.get(l)
        if left_block == right_block:
            lazy_b = self.lazy_b[left_block]
            lazy_c = self.lazy_c[left_block]
            for idx in range(l, r):
                value = self.values[idx] + lazy_b * idx + lazy_c
                if value < res:
                    res = value
            return res
        lazy_b = self.lazy_b[left_block]
        lazy_c = self.lazy_c[left_block]
        for idx in range(l, self.block_right[left_block]):
            value = self.values[idx] + lazy_b * idx + lazy_c
            if value < res:
                res = value
        lazy_b = self.lazy_b[right_block]
        lazy_c = self.lazy_c[right_block]
        for idx in range(self.block_left[right_block], r):
            value = self.values[idx] + lazy_b * idx + lazy_c
            if value < res:
                res = value
        for block in range(left_block + 1, right_block):
            self._ensure_block_min(block)
            if self.block_min[block] < res:
                res = self.block_min[block]
        return res

    def get(self, p: int) -> int:
        """Return ``a[p]``.

        Args:
            p: Index.

        Time Complexity:
            ``O(1)``

        Returns:
            The current value at p.

        Raises:
            AssertionError: If the position or interval is out of bounds.
        """
        assert 0 <= p < self.n
        block = self.block_id[p]
        return self.values[p] + self.lazy_b[block] * p + self.lazy_c[block]


class SegmentTreeBeats:
    """Segment tree beats for ``chmin/chmax/add/update`` and range statistics.

    Initially the array contains n zeros. Missing entries in build are reset to
    zero. Integers have no fixed magnitude limit. Empty min/max queries return
    pinf/ninf for compatibility; these constants do not bound real values.
    Missing second extrema and pending assignments use None internally.

    This is the classical specialized beats implementation for integer arrays
    supporting:

    - range ``chmin``
    - range ``chmax``
    - range ``add``
    - range assignment
    - range ``min`` / ``max`` / ``sum``

    The implementation is intentionally specialized rather than heavily
    abstracted. Segment tree beats relies on several coupled invariants
    involving the largest / second-largest, smallest / second-smallest, and
    their counts; turning those into a generic callback-based interface usually
    makes both the preconditions and the constant factors much worse.

    Attributes:
            n: Number of elements in the segment tree.
            log: Number of levels in the tree.
            size: Size of the underlying array (power of 2).
            hi: Maximum value in the segment.
            lo: Minimum value in the segment.
            hi2: Second maximum value, or None if all values are equal.
            lo2: Second minimum value, or None if all values are equal.
            nhi: Count of the maximum value in the segment.
            nlo: Count of the minimum value in the segment.
            sum: Sum of the values in the segment.
            added: Lazy value for range addition.
            updated: Pending assignment, or None if no assignment is pending.
            lt: Left endpoint of the segment.
            rt: Right endpoint of the segment.

    Time Complexity:
        - Construction: ``O(n)``
        - ``build``: ``O(n)``
        - ``range_chmax`` / ``range_chmin``: amortized ``O(log^2 n)``, worst-case ``O(n)``
        - ``range_add`` / ``range_set``: ``O(log n)``
        - ``range_max`` / ``range_min`` / ``range_sum`` / ``get`` / ``set``: ``O(log n)``
        - ``all_max`` / ``all_min`` / ``all_sum``: ``O(1)``

    Space Complexity:
        O(n + 1). Integer arithmetic is counted as O(1).
    """

    # Empty-query return values only; real elements may exceed these bounds.
    pinf = 1 << 60
    ninf = -(1 << 60)

    def __init__(self, n: int) -> None:
        """Initialize a segment tree beats instance with ``n`` elements.

        Args:
            n (int): Number of elements in the segment tree.

        Time Complexity:
            O(n) in the size of the processed input or stored data

        Raises:
            ValueError: If a capacity is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.log = max(0, n - 1).bit_length()
        self.size = 1 << self.log
        self.lt = [0] * (2 * self.size)
        self.rt = [0] * (2 * self.size)
        for i in range(self.size):
            self.lt[self.size + i] = i
            self.rt[self.size + i] = i + 1
        for i in range(self.size - 1, -1, -1):
            self.lt[i] = self.lt[i << 1]
            self.rt[i] = self.rt[i << 1 | 1]
        self.build([])

    def build(self, arr: Sequence[int]) -> None:
        """Build the tree from an initial array.

        Args:
            arr: At most n values. Omitted positions are reset to zero; pending updates are cleared.

        Time Complexity:
            O(n) in the size of the processed input or stored data

        Raises:
            AssertionError: If len(arr) > n.

        Returns:
            None.
        """
        assert len(arr) <= self.n
        capacity = 2 * self.size
        self.hi = [self.ninf] * capacity
        self.lo = [self.pinf] * capacity
        self.hi2: list[int | None] = [None] * capacity
        self.lo2: list[int | None] = [None] * capacity
        self.nhi = [0] * capacity
        self.nlo = [0] * capacity
        self.sum = [0] * capacity
        self.added = [0] * capacity
        self.updated: list[int | None] = [None] * capacity
        for i in range(self.n):
            value = arr[i] if i < len(arr) else 0
            leaf = self.size + i
            self.hi[leaf] = self.lo[leaf] = self.sum[leaf] = value
            self.nhi[leaf] = self.nlo[leaf] = 1
        for i in range(self.size - 1, 0, -1):
            self._merge(i)

    def _merge(self, k: int) -> None:
        left, right = k << 1, k << 1 | 1
        self.sum[k] = self.sum[left] + self.sum[right]
        if not self.nhi[left] or not self.nhi[right]:
            child = left if self.nhi[left] else right
            self.hi[k], self.hi2[k], self.nhi[k] = self.hi[child], self.hi2[child], self.nhi[child]
            self.lo[k], self.lo2[k], self.nlo[k] = self.lo[child], self.lo2[child], self.nlo[child]
            return
        if self.hi[left] < self.hi[right]:
            self.hi[k] = self.hi[right]
            self.nhi[k] = self.nhi[right]
            second = self.hi2[right]
            self.hi2[k] = self.hi[left] if second is None else max(self.hi[left], second)
        elif self.hi[left] > self.hi[right]:
            self.hi[k] = self.hi[left]
            self.nhi[k] = self.nhi[left]
            second = self.hi2[left]
            self.hi2[k] = self.hi[right] if second is None else max(second, self.hi[right])
        else:
            self.hi[k] = self.hi[left]
            self.nhi[k] = self.nhi[left] + self.nhi[right]
            sl, sr = self.hi2[left], self.hi2[right]
            self.hi2[k] = sr if sl is None else sl if sr is None else max(sl, sr)
        if self.lo[left] > self.lo[right]:
            self.lo[k] = self.lo[right]
            self.nlo[k] = self.nlo[right]
            second = self.lo2[right]
            self.lo2[k] = self.lo[left] if second is None else min(self.lo[left], second)
        elif self.lo[left] < self.lo[right]:
            self.lo[k] = self.lo[left]
            self.nlo[k] = self.nlo[left]
            second = self.lo2[left]
            self.lo2[k] = self.lo[right] if second is None else min(second, self.lo[right])
        else:
            self.lo[k] = self.lo[left]
            self.nlo[k] = self.nlo[left] + self.nlo[right]
            sl, sr = self.lo2[left], self.lo2[right]
            self.lo2[k] = sr if sl is None else sl if sr is None else min(sl, sr)

    def _propagate(self, k: int) -> None:
        if self.size <= k:
            return
        updated = self.updated[k]
        if updated is not None:
            self._update(k << 1, updated)
            self._update(k << 1 | 1, updated)
            self.updated[k] = None
            return
        if self.added[k]:
            self._add(k << 1, self.added[k])
            self._add(k << 1 | 1, self.added[k])
            self.added[k] = 0
        if self.nhi[k << 1] and self.hi[k] < self.hi[k << 1]:
            self._chmax(k << 1, self.hi[k])
        if self.nlo[k << 1] and self.lo[k << 1] < self.lo[k]:
            self._chmin(k << 1, self.lo[k])
        if self.nhi[k << 1 | 1] and self.hi[k] < self.hi[k << 1 | 1]:
            self._chmax(k << 1 | 1, self.hi[k])
        if self.nlo[k << 1 | 1] and self.lo[k << 1 | 1] < self.lo[k]:
            self._chmin(k << 1 | 1, self.lo[k])

    def _update(self, k: int, x: int) -> None:
        size = self.rt[k] - self.lt[k]
        self.hi[k] = x
        self.hi2[k] = None
        self.lo[k] = x
        self.lo2[k] = None
        self.nhi[k] = size
        self.nlo[k] = size
        self.sum[k] = x * size
        self.added[k] = 0
        self.updated[k] = x

    def _add(self, k: int, x: int) -> None:
        size = self.rt[k] - self.lt[k]
        self.hi[k] += x
        second = self.hi2[k]
        if second is not None:
            self.hi2[k] = second + x
        self.lo[k] += x
        second = self.lo2[k]
        if second is not None:
            self.lo2[k] = second + x
        self.sum[k] += x * size
        updated = self.updated[k]
        if updated is not None:
            self.updated[k] = updated + x
        else:
            self.added[k] += x

    def _chmax(self, k: int, x: int) -> None:
        self.sum[k] += (x - self.hi[k]) * self.nhi[k]
        if self.hi[k] == self.lo[k]:
            self.hi[k] = x
            self.lo[k] = x
        elif self.hi[k] == self.lo2[k]:
            self.hi[k] = x
            self.lo2[k] = x
        else:
            self.hi[k] = x
        updated = self.updated[k]
        if updated is not None and x < updated:
            self.updated[k] = x

    def _chmin(self, k: int, x: int) -> None:
        self.sum[k] += (x - self.lo[k]) * self.nlo[k]
        if self.lo[k] == self.hi[k]:
            self.lo[k] = x
            self.hi[k] = x
        elif self.lo[k] == self.hi2[k]:
            self.lo[k] = x
            self.hi2[k] = x
        else:
            self.lo[k] = x
        updated = self.updated[k]
        if updated is not None and updated < x:
            self.updated[k] = x

    def range_chmax(self, l: int, r: int, x: int) -> None:
        """Apply ``a_i = max(a_i, x)`` on ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.
            x: Integer value used by this operation.

        Time Complexity:
            Amortized O(log^2 n); O(n) for a single worst-case update.

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold.

        Returns:
            None.
        """
        assert 0 <= l <= r <= self.n
        stack = [1]
        order: list[int] = []
        while stack:
            k = stack.pop()
            if r <= self.lt[k] or self.rt[k] <= l or x <= self.lo[k]:
                continue
            second = self.lo2[k]
            if l <= self.lt[k] and self.rt[k] <= r and (second is None or x < second):
                self._chmin(k, x)
                continue
            order.append(k)
            self._propagate(k)
            stack.append(k << 1)
            stack.append(k << 1 | 1)
        for v in reversed(order):
            self._merge(v)

    def range_chmin(self, l: int, r: int, x: int) -> None:
        """Apply ``a_i = min(a_i, x)`` on ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.
            x: Integer value used by this operation.

        Time Complexity:
            Amortized O(log^2 n); O(n) for a single worst-case update.

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold.

        Returns:
            None.
        """
        assert 0 <= l <= r <= self.n
        stack = [1]
        order: list[int] = []
        while stack:
            k = stack.pop()
            if r <= self.lt[k] or self.rt[k] <= l or self.hi[k] <= x:
                continue
            second = self.hi2[k]
            if l <= self.lt[k] and self.rt[k] <= r and (second is None or second < x):
                self._chmax(k, x)
                continue
            order.append(k)
            self._propagate(k)
            stack.append(k << 1)
            stack.append(k << 1 | 1)
        for v in reversed(order):
            self._merge(v)

    def range_add(self, l: int, r: int, x: int) -> None:
        """Add ``x`` on ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.
            x: Integer value used by this operation.

        Time Complexity:
            O(log n)

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold.

        Returns:
            None.
        """
        assert 0 <= l <= r <= self.n
        stack = [1]
        order: list[int] = []
        while stack:
            k = stack.pop()
            if r <= self.lt[k] or self.rt[k] <= l:
                continue
            if l <= self.lt[k] and self.rt[k] <= r:
                self._add(k, x)
                continue
            order.append(k)
            self._propagate(k)
            stack.append(k << 1)
            stack.append(k << 1 | 1)
        for v in reversed(order):
            self._merge(v)

    def range_set(self, l: int, r: int, x: int) -> None:
        """Assign ``x`` on ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.
            x: Integer value used by this operation.

        Time Complexity:
            O(log n)

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold.

        Returns:
            None.
        """
        assert 0 <= l <= r <= self.n
        stack = [1]
        order: list[int] = []
        while stack:
            k = stack.pop()
            if r <= self.lt[k] or self.rt[k] <= l:
                continue
            if l <= self.lt[k] and self.rt[k] <= r:
                self._update(k, x)
                continue
            order.append(k)
            self._propagate(k)
            stack.append(k << 1)
            stack.append(k << 1 | 1)
        for v in reversed(order):
            self._merge(v)

    def range_max(self, l: int, r: int) -> int:
        """Return the maximum on ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.

        Time Complexity:
            O(log n)

        Returns:
            Maximum value, or ninf for an empty range.

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold.
        """
        assert 0 <= l <= r <= self.n
        stack = [1]
        if l == r:
            return self.ninf
        res = self.get(l)
        while stack:
            k = stack.pop()
            if r <= self.lt[k] or self.rt[k] <= l:
                continue
            if l <= self.lt[k] and self.rt[k] <= r:
                res = max(res, self.hi[k])
                continue
            self._propagate(k)
            stack.append(k << 1)
            stack.append(k << 1 | 1)
        return res

    def all_max(self) -> int:
        """Return the maximum on the whole array.

        Time Complexity:
            O(1)

        Returns:
            Maximum value, or ninf when n == 0.
        """
        return self.hi[1]

    def range_min(self, l: int, r: int) -> int:
        """Return the minimum on ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.

        Time Complexity:
            O(log n)

        Returns:
            Minimum value, or pinf for an empty range.

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold.
        """
        assert 0 <= l <= r <= self.n
        stack = [1]
        if l == r:
            return self.pinf
        res = self.get(l)
        while stack:
            k = stack.pop()
            if r <= self.lt[k] or self.rt[k] <= l:
                continue
            if l <= self.lt[k] and self.rt[k] <= r:
                res = min(res, self.lo[k])
                continue
            self._propagate(k)
            stack.append(k << 1)
            stack.append(k << 1 | 1)
        return res

    def all_min(self) -> int:
        """Return the minimum on the whole array.

        Time Complexity:
            O(1)

        Returns:
            Minimum value, or pinf when n == 0.
        """
        return self.lo[1]

    def range_sum(self, l: int, r: int) -> int:
        """Return the sum on ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.

        Time Complexity:
            O(log n)

        Returns:
            Sum over the range; zero for an empty range.

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold.
        """
        assert 0 <= l <= r <= self.n
        stack = [1]
        res = 0
        while stack:
            k = stack.pop()
            if r <= self.lt[k] or self.rt[k] <= l:
                continue
            if l <= self.lt[k] and self.rt[k] <= r:
                res += self.sum[k]
                continue
            self._propagate(k)
            stack.append(k << 1)
            stack.append(k << 1 | 1)
        return res

    def all_sum(self) -> int:
        """Return the sum on the whole array.

        Time Complexity:
            O(1)

        Returns:
            Sum of all values; zero when n == 0.
        """
        return self.sum[1]

    def get(self, p: int) -> int:
        """Return the value at index ``p``.

        Args:
            p: Index in the underlying sequence.

        Raises:
            AssertionError: If ``0 <= p < n`` is false.

        Time Complexity:
            O(log n)

        Returns:
            The value at p.
        """
        assert 0 <= p < self.n
        k = 1
        while k < self.size:
            self._propagate(k)
            mid = (self.lt[k] + self.rt[k]) >> 1
            if p < mid:
                k = k << 1
            else:
                k = k << 1 | 1
        return self.sum[k]

    def set(self, p: int, x: int) -> None:
        """Set the value at index ``p`` to ``x``.

        Args:
            p: Index in the underlying sequence.
            x: Integer value used by this operation.

        Raises:
            AssertionError: If ``0 <= p < n`` is false.

        Time Complexity:
            O(log n)

        Returns:
            None.
        """
        assert 0 <= p < self.n
        self.range_set(p, p + 1, x)


class SegmentTree2D(Generic[ValueT]):
    """Dense two-dimensional segment tree for point updates and rectangle products.

    op must be associative and commutative with identity e. The two dimensions
    are grouped independently, so noncommutative operations are not supported.
    Callbacks must not mutate their inputs. All cells initially equal e.
    Complexity bounds assume O(1) callbacks and fixed-size values; logarithms
    are interpreted as at least one for empty or singleton dimensions.

    Space Complexity:
        O((n + 1) * (m + 1)).
    """

    def __init__(self, n: int, m: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT) -> None:
        """Initialize a 2D segment tree with `n` rows and `m` columns.

        Args:
            n (int): Number of rows.
            m (int): Number of columns.
            op (Callable[[ValueT, ValueT], ValueT]): Associative and commutative operation for cells.
            e (ValueT): Two-sided identity for op.

        Time Complexity:
            O(nm) in the size of the processed input or stored data

        Raises:
            ValueError: If a capacity is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        if m < 0:
            raise ValueError('m must be nonnegative')
        self.m = m
        self.op = op
        self.e = e
        self.log_n = max(0, n - 1).bit_length()
        self.log_m = max(0, m - 1).bit_length()
        self.size_n = 1 << self.log_n
        self.size_m = 1 << self.log_m
        self.d = [[e] * (2 * self.size_m) for _ in range(2 * self.size_n)]

    def build(self, arr: Sequence[Sequence[ValueT]]) -> None:
        """Build the 2D segment tree from a matrix of elements.

        Args:
            arr (Sequence[Sequence[ValueT]]): Initial elements.

        Raises:
            AssertionError: If any of ``len(arr) == n``, ``all((len(row) == m for row in arr))`` is false.

        Time Complexity:
            O(n * m)

        Returns:
            None.
        """
        assert len(arr) == self.n
        assert all(len(row) == self.m for row in arr)
        for i in range(self.n):
            for j in range(self.m):
                self.d[i + self.size_n][j + self.size_m] = arr[i][j]
        for i in range(1, self.size_n)[::-1]:
            for j in range(self.size_m, self.size_m + self.m):
                self.d[i][j] = self.op(self.d[2 * i][j], self.d[2 * i + 1][j])
        for i in range(1, 2 * self.size_n):
            for j in range(1, self.size_m)[::-1]:
                self.d[i][j] = self.op(self.d[i][2 * j], self.d[i][2 * j + 1])

    def set(self, p: int, q: int, x: ValueT) -> None:
        """Set the element at position `(p, q)` to `x`.

        Args:
            p (int): Row index.
            q (int): Column index.
            x (ValueT): New value of the element.

        Raises:
            AssertionError: If any of ``0 <= p < n``, ``0 <= q < m`` is false.

        Time Complexity:
            O(log n log m)

        Returns:
            None.
        """
        assert 0 <= p < self.n
        assert 0 <= q < self.m
        p += self.size_n
        q += self.size_m
        self.d[p][q] = x
        for i in range(1, self.log_n + 1):
            row = p >> i
            self.d[row][q] = self.op(self.d[2 * row][q], self.d[2 * row + 1][q])
        for i in range(self.log_n + 1):
            row = self.d[p >> i]
            for j in range(1, self.log_m + 1):
                col = q >> j
                row[col] = self.op(row[2 * col], row[2 * col + 1])

    def get(self, p: int, q: int) -> ValueT:
        """Retrieve the element at position `(p, q)`.

        Args:
            p (int): Row index.
            q (int): Column index.

        Returns:
            ValueT: Value of the element at position `(p, q)`.

        Raises:
            AssertionError: If any of ``0 <= p < n``, ``0 <= q < m`` is false.

        Time Complexity:
            O(1)
        """
        assert 0 <= p < self.n
        assert 0 <= q < self.m
        return self.d[p + self.size_n][q + self.size_m]

    def prod(self, l: int, r: int, u: int, d: int) -> ValueT:
        """
        Compute the result of applying the binary operation over the submatrix [(l, u), (r, d)).

        Args:
            l (int): Left endpoint of the row (inclusive).
            r (int): Right endpoint of the row (exclusive).
            u (int): Upper endpoint of the column (inclusive).
            d (int): Lower endpoint of the column (exclusive).

        Returns:
            ValueT: Result of the binary operation over the submatrix.

        Raises:
            AssertionError: If any of ``0 <= l <= r <= n``, ``0 <= u <= d <= m`` is false.

        Time Complexity:
            O(log n * log m)
        """
        assert 0 <= l <= r <= self.n
        assert 0 <= u <= d <= self.m
        result = self.e
        rows: list[int] = []
        l += self.size_n
        r += self.size_n
        while l < r:
            if l & 1:
                rows.append(l)
                l += 1
            if r & 1:
                r -= 1
                rows.append(r)
            l >>= 1
            r >>= 1
        for p in rows:
            left, right = u + self.size_m, d + self.size_m
            row = self.d[p]
            while left < right:
                if left & 1:
                    result = self.op(result, row[left])
                    left += 1
                if right & 1:
                    right -= 1
                    result = self.op(result, row[right])
                left >>= 1
                right >>= 1
        return result

    def prod_single_row(self, p: int, u: int, d: int) -> ValueT:
        """Compute the result of applying the binary operation over the subrow [u, d).

        Args:
            p (int): Zero-based row index in the original matrix.
            u (int): Upper endpoint of the column (inclusive).
            d (int): Lower endpoint of the column (exclusive).

        Returns:
            ValueT: Result of the binary operation over the subrow.

        Time Complexity:
            O(log m)

        Raises:
            AssertionError: If p or [u, d) is out of bounds.
        """
        assert 0 <= p < self.n
        assert 0 <= u <= d <= self.m
        p += self.size_n
        sml = smr = self.e
        u += self.size_m
        d += self.size_m
        while u < d:
            if u & 1:
                sml = self.op(sml, self.d[p][u])
                u += 1
            if d & 1:
                d -= 1
                smr = self.op(self.d[p][d], smr)
            u >>= 1
            d >>= 1
        return self.op(sml, smr)

    def all_prod(self) -> ValueT:
        """Compute the result of applying the binary operation over the entire matrix.

        Returns:
            ValueT: Result of the binary operation over the matrix.

        Time Complexity:
            O(1)
        """
        return self.d[1][1]


class DualSegmentTree(Generic[ValueT]):
    """Dual segment tree for range updates and point queries.

    An update f replaces each covered value x by op(f, x). op must be
    associative with identity id, and op(f, g) applies g first, then f.
    Initially every value equals id. commutative=True permits skipping
    propagation before range updates; the caller must guarantee commutativity.
    Callbacks must not mutate their inputs. Complexity bounds assume O(1)
    callbacks and fixed-size values.

    Space Complexity:
        O(n + 1).
    """

    def __init__(self, n: int, op: Callable[[ValueT, ValueT], ValueT], id: ValueT, commutative: bool = False) -> None:
        """Initialize a dual segment tree with `n` elements.

        Args:
            n (int): Number of elements in the segment tree.
            op (Callable[[ValueT, ValueT], ValueT]): Binary operation used to combine elements.
            id (ValueT): Identity element for the binary operation `op`.
            commutative (bool): Whether the operation is commutative. Defaults to False. True skips propagation before range updates; the caller guarantees commutativity.

        Time Complexity:
            O(n) for initialization

        Raises:
            ValueError: If a capacity is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.op = op
        self.id = id
        self.log = max(0, n - 1).bit_length()
        self.size = 1 << self.log
        self.d = [id] * self.size
        self.lz = [id] * (2 * self.size)
        self.commutative = commutative

    def build(self, arr: Sequence[ValueT]) -> None:
        """Build the segment tree from a sequence of elements.

        Args:
            arr (Sequence[ValueT]): Exactly n elements; all previous values and pending updates are discarded.

        Raises:
            AssertionError: If ``len(arr) == n`` is false.

        Time Complexity:
            O(n)

        Returns:
            None.
        """
        assert len(arr) == self.n
        self.lz = [self.id] * (2 * self.size)
        for i, a in enumerate(arr):
            self.d[i] = a

    def _propagate(self, k: int) -> None:
        if self.lz[k] == self.id:
            return
        if k < self.size:
            self.lz[2 * k] = self.op(self.lz[k], self.lz[2 * k])
            self.lz[2 * k + 1] = self.op(self.lz[k], self.lz[2 * k + 1])
        else:
            self.d[k - self.size] = self.op(self.lz[k], self.d[k - self.size])
        self.lz[k] = self.id

    def get(self, p: int) -> ValueT:
        """
        Retrieve the element at position `p`.

        Args:
            p (int): Index of the element to retrieve.

        Returns:
            ValueT: Value of the element at position `p`.

        Raises:
            AssertionError: If ``0 <= p < n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= p < self.n
        res = self.d[p]
        p += self.size
        for i in range(self.log + 1):
            res = self.op(self.lz[p >> i], res)
        return res

    def range_apply(self, l: int, r: int, f: ValueT) -> None:
        """Apply an update `f` to all elements in the range [l, r) by left composition with op.

        Args:
            l (int): Left boundary.
            r (int): Right boundary.
            f (ValueT): Update to apply. Elements in the specified range will be updated to `op(f, current_value)`.

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(log n)

        Returns:
            None.
        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return
        l += self.size
        r += self.size
        if not self.commutative:
            for i in range(1, self.log + 1)[::-1]:
                self._propagate(l >> i)
                self._propagate((r - 1) >> i)
        while l < r:
            if l & 1:
                self.lz[l] = self.op(f, self.lz[l])
                l += 1
            if r & 1:
                r -= 1
                self.lz[r] = self.op(f, self.lz[r])
            l >>= 1
            r >>= 1

    def _all_propagate(self) -> None:
        for i in range(1, 2 * self.size):
            self._propagate(i)

    def all_apply(self, f: ValueT) -> None:
        """Apply a function to all elements of the segment tree.

        Args:
            f (ValueT): The function to be applied to all elements.

        Time Complexity:
            O(1)

        Returns:
            None.
        """
        self.lz[1] = self.op(f, self.lz[1])

    def get_all(self) -> list[ValueT]:
        """
        Retrieve all elements from the segment tree.

        Returns:
            list[ValueT]: List of all elements.

        Time Complexity:
            O(n)
        """
        self._all_propagate()
        return self.d[:self.n]


class LazySegmentTree(Generic[ValueT, ActionT]):
    """Lazy segment tree for point/range updates and ordered range products.

    op is associative with identity e and need not be commutative.
    mapping(f, op(a, b)) must equal op(mapping(f, a), mapping(f, b)), and
    mapping(f, e) must equal e. Include segment length in ValueT when an update
    such as addition to a sum depends on that length.
    composition(f, g) applies g first, then f, and id leaves values unchanged.
    Callbacks must not mutate their inputs. Initially all elements equal e.
    Complexity bounds assume O(1) callbacks and fixed-size values.

    Space Complexity:
        O(n + 1).
    """

    def __init__(self, n: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[[ActionT, ValueT], ValueT], composition: Callable[[ActionT, ActionT], ActionT], id: ActionT) -> None:
        """Initialize a lazy segment tree with `n` elements.

        Args:
            n (int): Number of elements in the segment tree.
            op (Callable[[ValueT, ValueT], ValueT]): Binary operation used to combine elements.
            e (ValueT): Identity element for the binary operation `op`.
            mapping (Callable[[ActionT, ValueT], ValueT]): Mapping function to apply updates.
            composition (Callable[[ActionT, ActionT], ActionT]): Composition function for multiple updates.
            id (ActionT): Identity element for updates.

        Time Complexity:
            O(n) for initialization

        Raises:
            ValueError: If a capacity is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.op = op
        self.e = e
        self.mapping = mapping
        self.composition = composition
        self.id = id
        self.log = max(0, n - 1).bit_length()
        self.size = 1 << self.log
        self.d = [e] * (2 * self.size)
        self.lz = [id] * (self.size)

    def _update(self, k: int) -> None:
        self.d[k] = self.op(self.d[2 * k], self.d[2 * k + 1])

    def _all_apply(self, k: int, f: ActionT) -> None:
        self.d[k] = self.mapping(f, self.d[k])
        if k < self.size:
            self.lz[k] = self.composition(f, self.lz[k])

    def _push(self, k: int) -> None:
        self._all_apply(2 * k, self.lz[k])
        self._all_apply(2 * k + 1, self.lz[k])
        self.lz[k] = self.id

    def build(self, arr: Sequence[ValueT]) -> None:
        """Build the segment tree from a sequence of elements.

        Args:
            arr (Sequence[ValueT]): Exactly n elements; all previous values and pending updates are discarded.

        Raises:
            AssertionError: If ``len(arr) == n`` is false.

        Time Complexity:
            O(n)

        Returns:
            None.
        """
        assert len(arr) == self.n
        self.lz = [self.id] * self.size
        for i, a in enumerate(arr):
            self.d[self.size + i] = a
        for i in range(1, self.size)[::-1]:
            self._update(i)

    def set(self, p: int, x: ValueT) -> None:
        """Set the value at position `p` to `x`.

        Args:
            p (int): Position.
            x (ValueT): Value to set.

        Raises:
            AssertionError: If ``0 <= p < n`` is false.

        Time Complexity:
            O(log n)

        Returns:
            None.
        """
        assert 0 <= p < self.n
        p += self.size
        for i in range(1, self.log + 1)[::-1]:
            self._push(p >> i)
        self.d[p] = x
        for i in range(1, self.log + 1):
            self._update(p >> i)

    def get(self, p: int) -> ValueT:
        """
        Retrieve the value at position `p`.

        Args:
            p (int): Position.

        Returns:
            ValueT: Value at position `p`.

        Raises:
            AssertionError: If ``0 <= p < n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= p < self.n
        p += self.size
        for i in range(1, self.log + 1)[::-1]:
            self._push(p >> i)
        return self.d[p]

    def prod(self, l: int, r: int) -> ValueT:
        """
        Compute the product in the range [l, r) using the binary operation.

        Args:
            l (int): Left boundary.
            r (int): Right boundary.

        Returns:
            ValueT: Computed product.

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return self.e
        l += self.size
        r += self.size
        for i in range(1, self.log + 1)[::-1]:
            if ((l >> i) << i) != l:
                self._push(l >> i)
            if ((r >> i) << i) != r:
                self._push(r >> i)
        sml = smr = self.e
        while l < r:
            if l & 1:
                sml = self.op(sml, self.d[l])
                l += 1
            if r & 1:
                r -= 1
                smr = self.op(self.d[r], smr)
            l >>= 1
            r >>= 1
        return self.op(sml, smr)

    def all_prod(self) -> ValueT:
        """
        Compute the product of all elements in the segment tree.

        Returns:
            ValueT: Computed product.

        Time Complexity:
            O(1)
        """
        return self.d[1]

    def apply(self, p: int, f: ActionT) -> None:
        """Apply an update `f` to the element at position `p` using the mapping function.

        Args:
            p (int): Position.
            f (ActionT): Update to apply. The element at position `p` will be updated to `mapping(f, current_value)`.

        Raises:
            AssertionError: If ``0 <= p < n`` is false.

        Time Complexity:
            O(log n)

        Returns:
            None.
        """
        assert 0 <= p < self.n
        p += self.size
        for i in range(1, self.log + 1)[::-1]:
            self._push(p >> i)
        self.d[p] = self.mapping(f, self.d[p])
        for i in range(1, self.log + 1):
            self._update(p >> i)

    def range_apply(self, l: int, r: int, f: ActionT) -> None:
        """Apply an update `f` to all elements in the range [l, r) using the mapping function.

        Args:
            l (int): Left boundary.
            r (int): Right boundary.
            f (ActionT): Update to apply. Elements in the specified range will be updated to `mapping(f, current_value)`.

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(log n)

        Returns:
            None.
        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return
        l += self.size
        r += self.size
        for i in range(1, self.log + 1)[::-1]:
            if ((l >> i) << i) != l:
                self._push(l >> i)
            if ((r >> i) << i) != r:
                self._push((r - 1) >> i)
        l2 = l
        r2 = r
        while l < r:
            if l & 1:
                self._all_apply(l, f)
                l += 1
            if r & 1:
                r -= 1
                self._all_apply(r, f)
            l >>= 1
            r >>= 1
        l = l2
        r = r2
        for i in range(1, self.log + 1):
            if ((l >> i) << i) != l:
                self._update(l >> i)
            if ((r >> i) << i) != r:
                self._update((r - 1) >> i)

    def max_right(self, l: int, g: Callable[[ValueT], bool]) -> int:
        """Find the maximum `r` such that `g(op(a[l], a[l+1], ..., a[r-1]))` is True.

        Args:
            l (int): Left endpoint (inclusive).
            g (Callable[[ValueT], bool]): A boolean function to satisfy.

        Returns:
            int: Maximum `r`.

        Raises:
            AssertionError: If any of ``0 <= l <= n``, ``g(e)`` is false.

        Time Complexity:
            O(log n)

        Notes:
            The predicate must be deterministic, accept e, and stay False once
            it becomes False as the queried interval is extended.
        """
        assert 0 <= l <= self.n
        assert g(self.e)
        if l == self.n:
            return self.n
        l += self.size
        for i in range(1, self.log + 1)[::-1]:
            self._push(l >> i)
        sm = self.e
        while True:
            while l % 2 == 0:
                l >>= 1
            if not g(self.op(sm, self.d[l])):
                while l < self.size:
                    self._push(l)
                    l = 2 * l
                    if g(self.op(sm, self.d[l])):
                        sm = self.op(sm, self.d[l])
                        l += 1
                return l - self.size
            sm = self.op(sm, self.d[l])
            l += 1
            if (l & -l) == l:
                return self.n

    def min_left(self, r: int, g: Callable[[ValueT], bool]) -> int:
        """Find the minimum `l` such that `g(op(a[l], a[l+1], ..., a[r-1]))` is True.

        Args:
            r (int): Right endpoint (exclusive).
            g (Callable[[ValueT], bool]): A boolean function to satisfy.

        Returns:
            int: Minimum `l`.

        Raises:
            AssertionError: If any of ``0 <= r <= n``, ``g(e)`` is false.

        Time Complexity:
            O(log n)

        Notes:
            The predicate must be deterministic, accept e, and stay False once
            it becomes False as the queried interval is extended.
        """
        assert 0 <= r <= self.n
        assert g(self.e)
        if r == 0:
            return 0
        r += self.size
        for i in range(1, self.log + 1)[::-1]:
            self._push((r - 1) >> i)
        sm = self.e
        while True:
            r -= 1
            while r > 1 and r % 2:
                r >>= 1
            if not g(self.op(self.d[r], sm)):
                while r < self.size:
                    self._push(r)
                    r = 2 * r + 1
                    if g(self.op(self.d[r], sm)):
                        sm = self.op(self.d[r], sm)
                        r -= 1
                return r + 1 - self.size
            sm = self.op(self.d[r], sm)
            if (r & -r) == r:
                return 0


class RangeAffineRangeSum:
    """Range affine updates and modular range sums over an initially zero array.

    The wrapper packs (sum modulo mod(), length modulo mod()) and affine
    coefficients into integers. mod must return the same positive integer
    throughout the lifetime of the structure, with 2 * mod() <= 2**31 - 1.
    Initial values may be arbitrary integers; update coefficients must lie
    in [0, mod()).

    Space Complexity:
        O(n + 1).
    """

    def __init__(self, n: int, mod: Callable[[], int]) -> None:
        """Initialize a data structure to handle range affine transformation and range sum queries.

        Args:
            n (int): Number of elements.
            mod (Callable[[], int]): Callable returning a fixed modulus, with 0 < 2 * mod() <= 2**31 - 1.

        Time Complexity:
            O(n)

        Examples:
            >>> mod = lambda: 7
            >>> tree = RangeAffineRangeSum(5, mod)
            >>> tree.build([10, 20, 30, 40, 50])
            >>> # 150 mod 7 = 3
            >>> tree.range_sum(0, 5)
            3

        Raises:
            ValueError: If a capacity is negative.
            AssertionError: If the modulus is nonpositive or exceeds the packing limit.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.mod = mod

        bitmask = (1 << 31) - 1
        assert 0 < self.mod() * 2 <= bitmask

        def op(l: int, r: int) -> int:
            lb, lc = l >> 31, l & bitmask
            rb, rc = r >> 31, r & bitmask
            return (((lb + rb) % self.mod()) << 31) + (lc + rc) % self.mod()

        def mapping(f: int, x: int) -> int:
            fb, fc = f >> 31, f & bitmask
            xb, xc = x >> 31, x & bitmask
            return (((fb * xb + fc * xc) % self.mod()) << 31) + xc

        def composition(f: int, g: int) -> int:
            fb, fc = f >> 31, f & bitmask
            gb, gc = g >> 31, g & bitmask
            return (((fb * gb) % self.mod()) << 31) + (fb * gc + fc) % self.mod()

        self.segtree = LazySegmentTree(n, op, 0, mapping, composition, 1 << 31)
        self.build([0] * n)

    def build(self, arr: Sequence[int]) -> None:
        """Build the data structure from a sequence of elements.

        Args:
            arr (Sequence[int]): Exactly n integers, replacing all previous values and pending updates.

        Time Complexity:
            O(n)

        Raises:
            AssertionError: If len(arr) != n.

        Returns:
            None.
        """
        assert len(arr) == self.n
        mod = self.mod()
        self.segtree.build([((a % mod) << 31) + 1 for a in arr])

    def range_affine(self, l: int, r: int, a: int, b: int) -> None:
        """Apply an affine transformation to all elements in the range [l, r).

        Args:
            l (int): Left boundary.
            r (int): Right boundary.
            a (int): Multiplier for the affine transformation.
            b (int): Addend for the affine transformation.

        Raises:
            AssertionError: If any of ``0 <= l <= r <= n``, ``0 <= a < mod()``, ``0 <= b < mod()`` is false.

        Time Complexity:
            O(log n)

        Returns:
            None.
        """
        assert 0 <= l <= r <= self.n
        assert 0 <= a < self.mod()
        assert 0 <= b < self.mod()
        self.segtree.range_apply(l, r, ((a << 31) + b))

    def range_sum(self, l: int, r: int) -> int:
        """
        Calculate the sum of elements in the range [l, r).

        Args:
            l (int): Left boundary.
            r (int): Right boundary.

        Returns:
            int: Computed sum.

        Raises:
            AssertionError: If ``0 <= l <= r <= n`` is false.

        Time Complexity:
            O(log n)
        """
        assert 0 <= l <= r <= self.n
        return self.segtree.prod(l, r) >> 31


class MergeSortTree(Generic[KeyT]):
    """Static range counts and aggregates of values at most a threshold.

    Each node stores sorted values and their prefix aggregates. Keys are
    ordered using <. op must be associative and commutative with identity e:
    the original sequence order is not preserved by sorting and grouping.
    Callbacks must not mutate their inputs. Complexity bounds assume O(1)
    comparisons and callbacks and fixed-size values.
    Before build, all positions contain no value and queries return (0, e).

    Args:
        n: Number of positions.
        op: Commutative associative operation for selected values.
        e: Identity element for op.

    Space Complexity:
        O(n log(n + 1) + 1) after build; O(n + 1) before build.
    """

    def __init__(self, n: int, op: Callable[[KeyT, KeyT], KeyT], e: KeyT) -> None:
        """Initialize an empty merge sort tree.

        Args:
            n: Number of elements.
            op: Associative and commutative operation for prefix aggregates.
            e: Identity element for ``op``.

        Time Complexity:
            O(n)

        Raises:
            ValueError: If a capacity is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.op = op
        self.e = e
        self.log = max(0, n - 1).bit_length()
        self.size = 1 << self.log
        self.tree: list[list[KeyT]] = [[] for _ in range(2 * self.size)]
        self.cumsum: list[list[KeyT]] = [[e] for _ in range(2 * self.size)]

    def _merge(self, lt: list[KeyT], rt: list[KeyT]) -> list[KeyT]:
        merged: list[KeyT] = []
        i, j = 0, 0
        while i < len(lt) and j < len(rt):
            if lt[i] < rt[j]:
                merged.append(lt[i])
                i += 1
            else:
                merged.append(rt[j])
                j += 1
        merged.extend(lt[i:])
        merged.extend(rt[j:])
        return merged

    def build(self, arr: list[KeyT]) -> None:
        """Build the tree from an initial sequence.

        Args:
            arr: Exactly n values, replacing all previous values.

        Time Complexity:
            O(n log n)

        Raises:
            AssertionError: If len(arr) != n.

        Returns:
            None.
        """
        assert len(arr) == self.n
        for i, t in enumerate(arr):
            self.tree[self.size + i] = [t]
        for i in range(1, self.size)[::-1]:
            self.tree[i] = self._merge(self.tree[2 * i], self.tree[2 * i + 1])
        for i in range(1, 2 * self.size):
            self.cumsum[i] = [self.e] * (len(self.tree[i]) + 1)
        for i in range(1, 2 * self.size):
            for j in range(len(self.tree[i])):
                self.cumsum[i][j + 1] = self.op(self.cumsum[i][j], self.tree[i][j])

    def prod_le(self, l: int, r: int, x: KeyT) -> tuple[int, KeyT]:
        """Count and aggregate values at most ``x`` in ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.
            x: Upper bound for included values.

        Returns:
            A pair ``(count, aggregate)`` where ``count`` is the number of
            values in ``[l, r)`` that are at most ``x`` and ``aggregate`` is
            their fold by ``op``.

        Time Complexity:
            O(log^2 n)

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold.
        """
        assert 0 <= l <= r <= self.n
        l += self.size
        r += self.size
        res = self.e
        cnt = 0
        while l < r:
            if l & 1:
                i = bisect_right(self.tree[l], x)
                res = self.op(res, self.cumsum[l][i])
                cnt += i
                l += 1
            if r & 1:
                r -= 1
                i = bisect_right(self.tree[r], x)
                res = self.op(res, self.cumsum[r][i])
                cnt += i
            l >>= 1
            r >>= 1
        return cnt, res
