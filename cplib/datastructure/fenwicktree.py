#!/usr/bin/env python3

from collections.abc import Callable, Sequence, Iterator
from typing import Generic
from bisect import bisect_left, bisect_right
from cplib.tools.type import KeyT, ValueT


class FenwickTree:
    """
    Fenwick Tree (Binary Indexed Tree) for efficient prefix sum queries.

    A data structure that supports point updates and prefix sum queries in O(log n) time.
    Also known as Binary Indexed Tree (BIT). Useful for problems involving range sum queries
    with updates.

    Attributes:
        n: Number of elements in the tree.
        data: Internal array storing the Fenwick Tree values.

    Examples:
        >>> ft = FenwickTree(5)
        >>> ft.build([1, 2, 3, 4, 5])
        >>> print(ft.sum(3))  # Sum of first 3 elements: 1+2+3 = 6
        6
        >>> ft.add(1, 10)     # Add 10 to element at index 1
        >>> print(ft.range_sum(1, 4))  # Sum of elements [1,4): (2+10)+3+4 = 19
        19
        >>> print(ft.bisect_left(10))  # First prefix length with sum >= 10
        2

    Notes:
        All indices are 0-based. The tree maintains prefix sums internally
        for efficient range queries.

    Space Complexity:
        O(n)
    """
    def __init__(self, n: int) -> None:
        """
        Initialize a Fenwick Tree with n nodes.

        Args:
            n (int): The number of nodes in the tree

        Raises:
            ValueError: If n is negative.

        Returns:
            None.

        Time Complexity:
            O(n)

        Examples:
            >>> ft = FenwickTree(5)
            >>> len(ft.data)
            5
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.data = [0] * n

    def build(self, arr: Sequence[int]) -> None:
        """
        Build the Fenwick Tree from an initial sequence of data.

        Args:
            arr (Sequence[int]): A sequence of integers to initialize the tree

        Raises:
            AssertionError: If len(arr) > n

        Notes:
            Replaces all previous values. Omitted positions are reset to zero.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        assert len(arr) <= self.n
        for i, a in enumerate(arr):
            self.data[i] = a
        for i in range(len(arr), self.n):
            self.data[i] = 0
        for i in range(1, self.n + 1):
            if i + (i & -i) <= self.n:
                self.data[i + (i & -i) - 1] += self.data[i - 1]

    def add(self, p: int, x: int) -> None:
        """
        Add a value x to the p-th position of the data.

        Args:
            p (int): The position in the data to add the value to
            x (int): The value to add

        Raises:
            AssertionError: If p is out of range [0, n)

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        assert 0 <= p < self.n
        p += 1
        while p <= self.n:
            self.data[p - 1] += x
            p += p & -p

    def sum(self, r: int) -> int:
        """
        Return the prefix sum up to the r-th position.

        Args:
            r (int): The position to compute the prefix sum up to (exclusive)

        Returns:
            int: The prefix sum of elements [0, r)

        Raises:
            AssertionError: If r is out of range [0, n]

        Time Complexity:
            O(log n)
        """
        assert 0 <= r <= self.n
        s = 0
        while r:
            s += self.data[r - 1]
            r -= r & -r
        return s

    def get(self, p: int) -> int:
        """
        Get the value at the p-th position.

        Args:
            p (int): The position to get the value from

        Returns:
            int: The value at the p-th position

        Time Complexity:
            O(log n)
        """
        return self.range_sum(p, p + 1)

    def set(self, p: int, x: int) -> None:
        """
        Set the value at the p-th position to x.

        Args:
            p (int): The position to set the value at
            x (int): The value to set

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        self.add(p, x - self.get(p))

    def range_sum(self, l: int, r: int) -> int:
        """
        Compute the sum of the values in the range [l, r).

        Args:
            l (int): The start of the range (inclusive)
            r (int): The end of the range (exclusive)

        Returns:
            int: The sum of the values in the range [l, r)

        Raises:
            AssertionError: If l > r or indices are out of bounds

        Time Complexity:
            O(log n)
        """
        assert 0 <= l <= r <= self.n
        return self.sum(r) - self.sum(l)

    def bisect_left(self, x: int) -> int:
        """
        Find the smallest position where the prefix sum is at least x.

        Args:
            x (int): The target prefix sum value

        Returns:
            int: The smallest position p such that sum(p) >= x, or n+1 if no such position exists

        Examples:
            >>> ft = FenwickTree(5)
            >>> ft.build([1, 2, 3, 4, 5])
            >>> ft.bisect_left(6)  # First position where prefix sum >= 6
            3

        Notes:
            All point values must be nonnegative so prefix sums are monotone.
            This precondition is not checked. Returns 0 when x <= 0.
            Uses binary lifting technique to efficiently find the position
            without calling sum() repeatedly.

        Time Complexity:
            O(log n)
        """
        if x <= 0:
            return 0
        res = 0
        k = 1 << self.n.bit_length()
        while k:
            if res + k <= self.n and self.data[res + k - 1] < x:
                x -= self.data[res + k - 1]
                res += k
            k >>= 1
        return res + 1


class GroupFenwickTree(Generic[ValueT]):
    """
    Fenwick tree over an abelian group.

    This is the group-valued version of :class:`FenwickTree`. It stores a
    sequence of values in an abelian group and supports point updates,
    prefix products, and range products in logarithmic time.

    Attributes:
        n: Number of elements in the tree.
        op: Group operation.
        inv: Inverse operation for the group.
        e: Identity element of the group.
        data: Internal array storing the Fenwick Tree values.

    Time Complexity:
        - Construction: ``O(n)``
        - ``build``: ``O(n)``
        - ``add`` / ``prefix_prod`` / ``prod`` / ``get`` / ``set``: ``O(log n)``

    Space Complexity:
        - ``O(n)``

    Examples:
        >>> ft = GroupFenwickTree(3, lambda a, b: a + b, lambda x: -x, 0)
        >>> ft.build([1, 2, 3])
        >>> ft.prod(0, 3)
        6
    """

    def __init__(self, n: int, op: Callable[[ValueT, ValueT], ValueT], inv: Callable[[ValueT], ValueT], e: ValueT) -> None:
        """
        Initialize a GroupFenwickTree.

        Args:
            n: Number of elements.
            op: Group operation.
            inv: Inverse operation for ``op``.
            e: Identity element of the group.

        Raises:
            ValueError: If n is negative.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.op = op
        self.inv = inv
        self.e = e
        self.data = [e] * n

    def build(self, arr: Sequence[ValueT]) -> None:
        """
        Build the Fenwick tree from an initial sequence.

        Args:
            arr: Initial values for the prefix-product structure.

        Raises:
            AssertionError: If ``len(arr) > n``.

        Notes:
            Replaces all previous values. Omitted positions are reset to the identity.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        assert len(arr) <= self.n
        for i, value in enumerate(arr):
            self.data[i] = value
        for i in range(len(arr), self.n):
            self.data[i] = self.e
        for i in range(1, self.n + 1):
            j = i + (i & -i)
            if j <= self.n:
                self.data[j - 1] = self.op(self.data[j - 1], self.data[i - 1])

    def add(self, p: int, value: ValueT) -> None:
        """
        Apply a group operation with ``value`` at index ``p``.

        Args:
            p: Index to update.
            value: Value to combine into ``a[p]``.

        Raises:
            AssertionError: If ``p`` is out of range.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        assert 0 <= p < self.n
        p += 1
        while p <= self.n:
            self.data[p - 1] = self.op(self.data[p - 1], value)
            p += p & -p

    def prefix_prod(self, r: int) -> ValueT:
        """
        Return the product of the prefix ``[0, r)``.

        Args:
            r: Exclusive right boundary of a range.

        Returns:
            Product of values in ``[0, r)``.

        Raises:
            AssertionError: If ``r`` is out of range.

        Time Complexity:
            O(log n)
        """
        assert 0 <= r <= self.n
        res = self.e
        while r:
            res = self.op(res, self.data[r - 1])
            r -= r & -r
        return res

    def get(self, p: int) -> ValueT:
        """
        Return the value at index ``p``.

        Args:
            p: Index in the underlying sequence.

        Returns:
            Value at index ``p``.

        Time Complexity:
            O(log n)
        """
        return self.prod(p, p + 1)

    def set(self, p: int, value: ValueT) -> None:
        """
        Set the value at index ``p``.

        Args:
            p: Index in the underlying sequence.
            value: New value to store.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        self.add(p, self.op(value, self.inv(self.get(p))))

    def prod(self, l: int, r: int) -> ValueT:
        """
        Return the product of the range ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.

        Returns:
            Product of values in ``[l, r)``.

        Raises:
            AssertionError: If the range is out of bounds.

        Time Complexity:
            O(log n)
        """
        assert 0 <= l <= r <= self.n
        return self.op(self.prefix_prod(r), self.inv(self.prefix_prod(l)))


class RangeAddPointGet:
    """
    Range add and point get data structure using Fenwick Tree.

    Supports efficient range addition and point queries using the difference array technique.
    Instead of storing actual values, stores differences between consecutive elements.

    Time Complexities:
        - range_add: O(log n)
        - get: O(log n)

    Examples:
        >>> rapg = RangeAddPointGet(5)
        >>> rapg.range_add(1, 4, 3)  # Add 3 to range [1, 4)
        >>> rapg.range_add(0, 2, 5)  # Add 5 to range [0, 2)
        >>> print(rapg.get(1))  # Get value at position 1: 3 + 5 = 8
        8

    Notes:
        Uses difference array technique: to add x to range [l, r),
        add x to position l and subtract x from position r.

    Args:
        n: Number of positions in the storage domain.

    Space Complexity:
        O(n)
    """
    def __init__(self, n: int) -> None:
        """
        Initialize range add point get structure.

        Raises:
            ValueError: If n is negative.

        Returns:
            None.

        Time Complexity: O(n)

        Args:
            n (int): Number of elements
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.bit = FenwickTree(n + 1)

    def range_add(self, l: int, r: int, x: int) -> None:
        """
        Add value x to all elements in range [l, r).

        Args:
            l (int): Left boundary (inclusive)
            r (int): Right boundary (exclusive)
            x (int): Value to add

        Raises:
            AssertionError: If 0 <= l <= r <= n does not hold; contents are unchanged.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return
        self.bit.add(l, x)
        self.bit.add(r, -x)

    def get(self, p: int) -> int:
        """
        Get the current value at position p.

        Args:
            p (int): Position to query

        Returns:
            int: Current value at position p

        Raises:
            AssertionError: If p is outside [0, n).

        Time Complexity:
            O(log n)
        """
        assert 0 <= p < self.n
        return self.bit.sum(p + 1)

    def build(self, arr: Sequence[int]) -> None:
        """
        Build the structure from an initial array.

        Args:
            arr (Sequence[int]): Initial array of values

        Notes:
            Converts the array to difference array format for efficient range updates.

        Notes:
            Replaces all previous values. Omitted positions are reset to zero.

        Raises:
            AssertionError: If len(arr) > n; contents are unchanged.

        Returns:
            None.

        Time Complexity:
            O(n) in the size of the processed input or stored data
        """
        assert len(arr) <= self.n
        bit_arr = [0] * (self.n + 1)
        for i in range(len(arr)):
            bit_arr[i] = arr[i] - (arr[i - 1] if i else 0)
        if arr:
            bit_arr[len(arr)] = -arr[-1]
        self.bit.build(bit_arr)


class GroupRangeAddPointGet(Generic[ValueT]):
    """
    Range add and point get over an abelian group.

    The structure stores a difference array inside a :class:`GroupFenwickTree`
    and exposes the usual half-open range addition API.


    Time Complexity:
        - Construction: ``O(n)``
        - ``range_add`` / ``get``: ``O(log n)``
        - ``build``: ``O(n)``

    Space Complexity:
        - ``O(n)``

    Examples:
        >>> ds = GroupRangeAddPointGet(3, lambda a, b: a + b, lambda x: -x, 0)
        >>> ds.build([1, 2, 3])
        >>> ds.range_add(1, 3, 10)
        >>> ds.get(2)
        13
    """

    def __init__(self, n: int, op: Callable[[ValueT, ValueT], ValueT], inv: Callable[[ValueT], ValueT], e: ValueT) -> None:
        """
        Initialize the structure.

        Args:
            n: Number of positions.
            op: Group operation.
            inv: Inverse operation for ``op``.
            e: Identity element of the group.

        Raises:
            ValueError: If n is negative.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.op = op
        self.inv = inv
        self.e = e
        self.bit = GroupFenwickTree(n + 1, op, inv, e)

    def range_add(self, l: int, r: int, value: ValueT) -> None:
        """
        Apply ``value`` to every position in ``[l, r)``.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.
            value: Value to combine into each position.

        Raises:
            AssertionError: If the range is out of bounds.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        assert 0 <= l <= r <= self.n
        if l == r:
            return
        self.bit.add(l, value)
        self.bit.add(r, self.inv(value))

    def get(self, p: int) -> ValueT:
        """
        Return the current value at index ``p``.

        Args:
            p: Index in the underlying sequence.

        Returns:
            Current value at ``p``.

        Raises:
            AssertionError: If ``p`` is out of range.

        Time Complexity:
            O(log n)
        """
        assert 0 <= p < self.n
        return self.bit.prefix_prod(p + 1)

    def build(self, arr: Sequence[ValueT]) -> None:
        """
        Build the structure from an initial sequence.

        Args:
            arr: Initial values.

        Raises:
            AssertionError: If ``len(arr) > n``.

        Notes:
            Replaces all previous values. Omitted positions are reset to the identity.

        Returns:
            None.

        Time Complexity:
            O(n) in the size of the processed input or stored data
        """
        assert len(arr) <= self.n
        bit_arr = [self.e] * (self.n + 1)
        if arr:
            bit_arr[0] = arr[0]
            for i in range(1, len(arr)):
                bit_arr[i] = self.op(arr[i], self.inv(arr[i - 1]))
            bit_arr[len(arr)] = self.inv(arr[-1])
        self.bit.build(bit_arr)


class RangeSetBIT:
    """
    Range-based set data structure using Fenwick Tree for order statistics.

    Maintains a set of integers in range [0, n) with efficient operations for:
    - Adding/removing elements
    - Finding k-th smallest element
    - Checking membership
    - Finding predecessors/successors

    Time Complexities:
        - add/discard: O(log n)
        - __contains__: O(log n)
        - __getitem__ (k-th element): O(log n)
        - predecessor/successor: O(log n)

    Examples:
        >>> s = RangeSetBIT(10)
        >>> s.add(3)
        True
        >>> s.add(7)
        True
        >>> s.add(1)
        True
        >>> print(len(s))  # 3
        3
        >>> print(s[0])    # 1 (smallest element)
        1
        >>> print(s[1])    # 3 (second smallest)
        3
        >>> print(7 in s)  # True
        True

    Notes:
        Elements must be integers in range [0, n).
        Maintains elements in sorted order for efficient k-th queries.

    Args:
        n: Number of positions in the storage domain.

    Space Complexity:
        O(n) in the constructor input size or configured capacity
    """
    def __init__(self, n: int) -> None:
        """
        Initialize range-based set for integers in [0, n).

        Args:
            n: Upper bound (exclusive) for valid elements

        Raises:
            ValueError: If n is negative.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.n = n
        self.bit = FenwickTree(n)

    def __str__(self) -> str:
        """
        Return string representation of the set.

        Returns:
            String representation showing all elements in sorted order

        Time Complexity:
            O(m log(n + 1)), where m is the number of stored elements and n is the capacity
        """
        return [self[i] for i in range(len(self))].__str__()

    def __len__(self) -> int:
        """
        Get the number of elements in the set.

        Time Complexity: O(log n)

        Returns:
            int: Number of elements in the set
        """
        return self.bit.range_sum(0, self.n)

    def __contains__(self, v: int) -> bool:
        """
        Check if value v is in the set.

        Time Complexity: O(log n)

        Args:
            v (int): Value to check

        Returns:
            bool: True if v is in the set, False otherwise, including values outside the storage domain
        """
        return 0 <= v < self.n and self.bit.get(v) == 1

    def __getitem__(self, i: int) -> int:
        """
        Get the i-th smallest element in the set.

        Time Complexity: O(log n)

        Args:
            i (int): Index (0-based) of element to retrieve

        Returns:
            int: The i-th smallest element

        Raises:
            IndexError: If i is out of range [0, len(self))
        """
        if not 0 <= i < len(self):
            raise IndexError('set index out of range')
        return self.bit.bisect_left(i + 1) - 1

    def __iter__(self) -> Iterator[int]:
        """
        Iterate over elements in sorted order.

        Time Complexity: O(m log(n + 1)), where m is the number of stored elements and n is the capacity

        Returns:
            Iterator[int]: Iterator over all elements in sorted order
        """
        return iter([self[i] for i in range(len(self))])

    def build(self, arr: Sequence[bool]) -> None:
        """
        Build the set from a boolean array.

        Args:
            arr (Sequence[bool]): Boolean array where arr[i] indicates if i is in the set

        Notes:
            Replaces all previous values. Omitted positions are reset to False.

        Raises:
            AssertionError: If len(arr) > n; contents are unchanged.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.bit.build(arr)

    def add(self, v: int) -> bool:
        """
        Add element v to the set.

        Args:
            v: Element to add, in [0, n).

        Returns:
            bool: True if element was added, False if already present

        Raises:
            AssertionError: If v is outside [0, n).

        Time Complexity:
            O(log n)
        """
        if v in self: return False
        self.bit.add(v, 1)
        return True

    def discard(self, v: int) -> bool:
        """
        Remove the specified value if present.

        Args:
            v: Value to remove.

        Returns:
            True if removed, otherwise False.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if not 0 <= v < self.n:
            return False
        if not self.bit.get(v):
            return False
        self.bit.add(v, -1)
        return True

    def remove(self, v: int) -> None:
        """
        Remove the specified value.

        Args:
            v: Value to remove.

        Returns:
            None.

        Raises:
            KeyError: If the value is absent.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if not self.discard(v):
            raise KeyError(v)

    def pop(self, i: int) -> int:
        """
        Remove and return the i-th smallest element.

        Args:
            i (int): Index of element to remove

        Returns:
            int: The removed element

        Raises:
            IndexError: If i is outside [0, len(self)); contents are unchanged.

        Time Complexity:
            O(log n)
        """
        if not 0 <= i < len(self):
            raise IndexError('pop index out of range')
        v = self.bit.bisect_left(i + 1) - 1
        self.bit.add(v, -1)
        return v

    def index(self, v: int) -> int:
        """
        Return the first sorted index of ``v``.

        Args:
            v: Search value.

        Returns:
            Zero-based index of the first occurrence.

        Raises:
            ValueError: If the value is absent.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if not 0 <= v < self.n or self.bit.get(v) == 0:
            raise ValueError('given value is not contained')
        return self.bit.sum(v)

    def bisect_left(self, v: int) -> int:
        """
        Return the number of elements strictly less than ``v``.

        Args:
            v: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        return self.bit.sum(max(0, min(v, self.n)))

    def bisect_right(self, v: int) -> int:
        """
        Return the number of elements less than or equal to ``v``.

        Args:
            v: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        return self.bit.sum(max(0, min(v + 1, self.n)))

    def max(self) -> int:
        """
        Get the maximum element in the set.

        Returns:
            int: Maximum element

        Raises:
            IndexError: If the container is empty.

        Time Complexity:
            O(log n)
        """
        return self[len(self) - 1]

    def min(self) -> int:
        """
        Get the minimum element in the set.

        Returns:
            int: Minimum element

        Raises:
            IndexError: If the container is empty.

        Time Complexity:
            O(log n)
        """
        return self[0]

    def median(self, upper: bool = False) -> int:
        """
        Get the median element in the set.

        Args:
            upper: If True, return the upper median when the size is even.
                   Otherwise, return the lower median.

        Returns:
            int: Median element.

        Raises:
            IndexError: If the set is empty.

        Time Complexity:
            O(log n)
        """
        m = len(self)
        if m == 0: raise IndexError
        return self[m // 2 if upper else (m - 1) // 2]

    def predecessor(self, v: int, inclusive: bool = True) -> int | None:
        """Return the largest stored value less than or equal to ``v``.

        Args:
            v: Search value; it may be absent or outside the storage range.
            inclusive: If False, require a value strictly less than v.

        Returns:
            Matching stored value, or None if no such value exists.

        Notes:
            Ordering uses only <. If inclusive is False, all values equivalent
            to the search value under this ordering are skipped.

        Time Complexity:
            O(log n), where n is the configured capacity.

        Space Complexity:
            O(1) auxiliary space.
        """
        pos = min(self.n, max(0, v + 1 if inclusive else v))
        index = self.bit.bisect_left(self.bit.sum(pos)) - 1
        if not 0 <= index < self.n:
            return None
        return index

    def successor(self, v: int, inclusive: bool = True) -> int | None:
        """Return the smallest stored value greater than or equal to ``v``.

        Args:
            v: Search value; it may be absent or outside the storage range.
            inclusive: If False, require a value strictly greater than v.

        Returns:
            Matching stored value, or None if no such value exists.

        Notes:
            Ordering uses only <. If inclusive is False, all values equivalent
            to the search value under this ordering are skipped.

        Time Complexity:
            O(log n), where n is the configured capacity.

        Space Complexity:
            O(1) auxiliary space.
        """
        pos = min(self.n, max(0, v if inclusive else v + 1))
        index = self.bit.bisect_left(self.bit.sum(pos) + 1) - 1
        if not 0 <= index < self.n:
            return None
        return index


class RangeMultisetBIT:
    """
    Range-based multiset data structure using Fenwick Tree.

    Similar to RangeSetBIT but allows multiple copies of the same element.
    Maintains a multiset of integers in range [0, n) with efficient operations for:
    - Adding/removing elements (with multiplicity)
    - Finding k-th smallest element
    - Checking membership
    - Order statistics

    Time Complexities:
        - add/discard: O(log n)
        - __contains__: O(log n)
        - __getitem__ (k-th element): O(log n)
        - count: O(log n)

    Examples:
        >>> ms = RangeMultisetBIT(10)
        >>> ms.add(3, 2)  # Add two copies of 3
        2
        >>> ms.add(7, 1)  # Add one copy of 7
        1
        >>> ms.add(3, 1)  # Add one more copy of 3
        1
        >>> print(len(ms))     # 4 (total elements)
        4
        >>> print(ms[0])       # 3 (smallest)
        3
        >>> print(ms[1])       # 3 (second smallest)
        3
        >>> print(ms[2])       # 3 (third smallest)
        3
        >>> print(ms[3])       # 7 (largest)
        7
        >>> print(ms.count(3)) # 3 (count of element 3)
        3

    Notes:
        Elements must be integers in range [0, n).
        Each position can store multiple copies of the same value.

    Args:
        n: Number of positions in the storage domain.

    Space Complexity:
        O(n) in the constructor input size or configured capacity
    """
    def __init__(self, n: int) -> None:
        """
        Initialize range-based multiset for integers in [0, n).

        Raises:
            ValueError: If n is negative.

        Returns:
            None.

        Time Complexity: O(n)

        Args:
            n (int): Upper bound (exclusive) for valid elements
        """
        self.n = n
        self.bit = FenwickTree(n)

    def __str__(self) -> str:
        """
        Return string representation of the multiset.

        Time Complexity: O(m log(n + 1)), where m is the number of stored elements and n is the capacity

        Returns:
            str: String representation showing all elements in sorted order
        """
        return [self[i] for i in range(len(self))].__str__()

    def __len__(self) -> int:
        """
        Get the total number of elements in the multiset.

        Time Complexity: O(log n)

        Returns:
            int: Total number of elements (including duplicates)
        """
        return self.bit.range_sum(0, self.n)

    def __contains__(self, v: int) -> bool:
        """
        Check if value v exists in the multiset.

        Time Complexity: O(log n)

        Args:
            v (int): Value to check

        Returns:
            bool: True if v exists (count > 0), False otherwise, including values outside the storage domain
        """
        return 0 <= v < self.n and self.bit.get(v) > 0

    def __getitem__(self, i: int) -> int:
        """
        Get the i-th smallest element in the multiset.

        Time Complexity: O(log n)

        Args:
            i (int): Index (0-based) of element to retrieve

        Returns:
            int: The i-th smallest element (counting duplicates)

        Raises:
            IndexError: If i is out of range [0, len(self))
        """
        if not 0 <= i < len(self): raise IndexError
        return self.bit.bisect_left(i + 1) - 1

    def __iter__(self) -> Iterator[int]:
        """
        Iterate over all elements in sorted order (including duplicates).

        Time Complexity: O(m log(n + 1)), where m is the number of stored elements and n is the capacity

        Returns:
            Iterator[int]: Iterator over all elements
        """
        return iter([self[i] for i in range(len(self))])

    def build(self, arr: Sequence[int]) -> None:
        """
        Build the multiset from an initial array of counts.

        Args:
            arr (Sequence[int]): Array where arr[i] is the count of element i

        Raises:
            ValueError: If len(arr) != n or any count is negative.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        if len(arr) != self.n:
            raise ValueError('length of arr must be equal to n')
        if any(count < 0 for count in arr):
            raise ValueError('counts must be nonnegative')
        self.bit.build(arr)

    def add(self, v: int, count: int = 1) -> int:
        """
        Add ``count`` copies of the value to the multiset.

        Args:
            v: Value to add, in [0, n) when count is positive.
            count: Number of copies to add. Zero is a no-op, even if v is out of range.

        Returns:
            Number of copies added, equal to ``count``.

        Raises:
            ValueError: If ``count`` is negative. The contents remain unchanged.
            AssertionError: If count is positive and v is outside [0, n).

        Time Complexity:
            O(log n), where n is the configured capacity; O(1) if count is zero.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return 0
        self.bit.add(v, count)
        return count

    def discard(self, v: int, count: int = 1) -> int:
        """
        Remove up to ``count`` copies.

        Args:
            v: Value to remove.
            count: Maximum number of copies to remove. Zero is a no-op.

        Returns:
            Number of copies actually removed; zero if the value is absent.

        Raises:
            ValueError: If ``count`` is negative.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return 0
        if not 0 <= v < self.n:
            return 0
        removed = min(count, self.bit.get(v))
        if removed:
            self.bit.add(v, -removed)
        return removed

    def remove(self, v: int, count: int = 1, validity_check: bool = True) -> None:
        """
        Remove exactly ``count`` copies.

        Args:
            v: Value to remove.
            count: Number of copies to remove. Zero is a no-op.
            validity_check: If False, the caller guarantees that at least ``count`` copies exist.

        Returns:
            None.

        Raises:
            KeyError: If ``validity_check=True`` and too few copies exist. The contents remain unchanged.
            ValueError: If ``count`` is negative.

        Notes:
            With ``validity_check=False``, the availability lookup is skipped.
            The caller must establish that the requested copies exist.
            Negative counts are rejected in either mode.

        Examples:
            >>> values = RangeMultisetBIT(8)
            >>> _ = values.add(5, 3)
            >>> values.discard(5, count=2)
            2
            >>> values.remove(5, count=2)
            Traceback (most recent call last):
                ...
            KeyError: 5
            >>> values.count(5)
            1
            >>> values.remove(5, validity_check=False)
            >>> values.count(5)
            0

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return
        if not 0 <= v < self.n or (validity_check and self.bit.get(v) < count):
            raise KeyError(v)
        self.bit.add(v, -count)

    def pop(self, i: int) -> int:
        """
        Remove and return the i-th smallest element.

        Args:
            i (int): Index of element to remove

        Returns:
            int: The removed element

        Raises:
            IndexError: If i is out of range [0, len(self))

        Time Complexity:
            O(log n)
        """
        if not 0 <= i < len(self): raise IndexError
        v = self.bit.bisect_left(i + 1) - 1
        self.bit.add(v, -1)
        return v

    def count(self, v: int) -> int:
        """
        Get the count of element v in the multiset.

        Args:
            v (int): Element to count

        Returns:
            int: Number of occurrences; zero if v is outside [0, n)

        Time Complexity:
            O(log n)
        """
        return self.bit.get(v) if 0 <= v < self.n else 0

    def index(self, v: int) -> int:
        """
        Return the first sorted index of ``v``.

        Args:
            v: Search value.

        Returns:
            Zero-based index of the first occurrence.

        Raises:
            ValueError: If the value is absent.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if not 0 <= v < self.n or self.bit.get(v) == 0:
            raise ValueError('given value is not contained')
        return self.bit.sum(v)

    def bisect_left(self, v: int) -> int:
        """
        Return the number of elements strictly less than ``v``.

        Args:
            v: Search value.

        Returns:
            Insertion index in sorted order, counting each copy separately.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        return self.bit.sum(max(0, min(v, self.n)))

    def bisect_right(self, v: int) -> int:
        """
        Return the number of elements less than or equal to ``v``.

        Args:
            v: Search value.

        Returns:
            Insertion index in sorted order, counting each copy separately.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        return self.bit.sum(max(0, min(v + 1, self.n)))

    def max(self) -> int:
        """
        Get the maximum element in the multiset.

        Returns:
            int: Maximum element

        Raises:
            IndexError: If the container is empty.

        Time Complexity:
            O(log n)
        """
        return self[len(self) - 1]

    def min(self) -> int:
        """
        Get the minimum element in the multiset.

        Returns:
            int: Minimum element

        Raises:
            IndexError: If the container is empty.

        Time Complexity:
            O(log n)
        """
        return self[0]

    def median(self, upper: bool = False) -> int:
        """
        Get the median element in the multiset.

        Args:
            upper: If True, return the upper median when the size is even.
                   Otherwise, return the lower median.

        Returns:
            int: Median element.

        Raises:
            IndexError: If the multiset is empty.

        Time Complexity:
            O(log n)
        """
        m = len(self)
        if m == 0: raise IndexError
        return self[m // 2 if upper else (m - 1) // 2]

    def predecessor(self, v: int, inclusive: bool = True) -> int | None:
        """Return the largest stored value less than or equal to ``v``.

        Args:
            v: Search value; it may be absent or outside the storage range.
            inclusive: If False, require a value strictly less than v.

        Returns:
            Matching stored value, or None if no such value exists.

        Notes:
            Ordering uses only <. If inclusive is False, all values equivalent
            to the search value under this ordering are skipped.

        Time Complexity:
            O(log n), where n is the configured capacity.

        Space Complexity:
            O(1) auxiliary space.
        """
        pos = min(self.n, max(0, v + 1 if inclusive else v))
        index = self.bit.bisect_left(self.bit.sum(pos)) - 1
        if not 0 <= index < self.n:
            return None
        return index

    def successor(self, v: int, inclusive: bool = True) -> int | None:
        """Return the smallest stored value greater than or equal to ``v``.

        Args:
            v: Search value; it may be absent or outside the storage range.
            inclusive: If False, require a value strictly greater than v.

        Returns:
            Matching stored value, or None if no such value exists.

        Notes:
            Ordering uses only <. If inclusive is False, all values equivalent
            to the search value under this ordering are skipped.

        Time Complexity:
            O(log n), where n is the configured capacity.

        Space Complexity:
            O(1) auxiliary space.
        """
        pos = min(self.n, max(0, v if inclusive else v + 1))
        index = self.bit.bisect_left(self.bit.sum(pos) + 1) - 1
        if not 0 <= index < self.n:
            return None
        return index


class SortedSetBIT(Generic[KeyT]):
    """
    Sorted set data structure for arbitrary comparable elements using Fenwick Tree.

    A set implementation that maintains elements in sorted order and supports
    efficient order statistics. Works with any comparable type, not just integers.

    Attributes:
        n: Number of possible distinct values (size of the variables list).
        variables: A sorted list of all possible values that can be in the set.
        bit: A Fenwick Tree that tracks which variables are currently in the set.

    Time Complexities:
        - add/discard: O(log n)
        - __contains__: O(log n)
        - __getitem__ (k-th element): O(log n)
        - index/bisect_left: O(log n)
        - predecessor/successor: O(log n)

    Examples:
        >>> # String set
        >>> s = SortedSetBIT(['apple', 'banana', 'cherry', 'date'])
        >>> s.add('banana')
        True
        >>> s.add('date')
        True
        >>> print(len(s))  # 2
        2
        >>> print(s[0])    # 'banana' (smallest)
        banana
        >>> print('cherry' in s)  # False
        False

        >>> # Float set
        >>> s = SortedSetBIT([1.1, 2.5, 3.7, 4.2, 5.9])
        >>> s.add(2.5)
        True
        >>> s.add(4.2)
        True
        >>> print(s.index(4.2))  # Index of 4.2 in the set
        1

    Notes:
        All possible values must be specified at initialization.
        Only values from the variables list can be added to the set.

    Space Complexity:
        O(n) in the constructor input size or configured capacity

    """
    def __init__(self, variables: list[KeyT]) -> None:
        """
        Initialize the sorted set with a list of possible variables.
        Args:
            variables (list[KeyT]): A sorted list of all possible values that can be in the set

        Raises:
            ValueError: If variables is not strictly increasing under <

        Notes:
            Copies the candidate list. Ordering equivalence uses <, without requiring __eq__.

        Returns:
            None.

        Time Complexity:
            O(n) in the size of the input list
        """
        if any(not a < b for a, b in zip(variables, variables[1:])):
            raise ValueError('variables must be sorted')
        self.n = len(variables)
        self.variables = variables[:]
        self.bit = FenwickTree(self.n)

    def _findpos(self, v: KeyT) ->tuple[int, bool]:
        """
        Find position of value v in the variables list.

        Time Complexity: O(log n)

        Args:
            v (KeyT): Value to find

        Returns:
            tuple[int, bool]: (position, found) where position is the index
                            and found indicates if the equivalent key under < was found
        """
        p = bisect_left(self.variables, v)
        if p == self.n or v < self.variables[p]: return p, False
        return p, True

    def build(self, arr: Sequence[bool]) -> None:
        """
        Build the set from a boolean array indicating which variables are present.

        Args:
            arr (Sequence[bool]): Boolean array where arr[i] indicates if variables[i] is in the set

        Raises:
            ValueError: If len(arr) != length of variables list

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        if len(arr) != self.n:
            raise ValueError('length of arr must be equal to length of variables')
        self.bit.build(arr)

    def __str__(self) -> str:
        """
        Return string representation of the set.

        Time Complexity: O(m log(n + 1)), where m is the number of stored elements and n is the capacity

        Returns:
            str: String representation showing all elements in sorted order
        """
        return [self[i] for i in range(len(self))].__str__()

    def __len__(self) -> int:
        """
        Get the number of elements in the set.

        Time Complexity: O(log n)

        Returns:
            int: Number of elements in the set
        """
        return self.bit.range_sum(0, self.n)

    def __contains__(self, v: KeyT) -> bool:
        """
        Check if value v is in the set.

        Time Complexity: O(log n)

        Args:
            v (KeyT): Value to check

        Returns:
            bool: True if v is in the set, False otherwise, including values outside the storage domain
        """
        pos, found = self._findpos(v)
        if not found: return False
        return self.bit.get(pos) == 1

    def __getitem__(self, i: int) -> KeyT:
        """
        Get the i-th smallest element in the set.

        Time Complexity: O(log n)

        Args:
            i (int): Index (0-based) of element to retrieve

        Returns:
            KeyT: The i-th smallest element

        Raises:
            IndexError: If i is out of range [0, len(self))
        """
        if not 0 <= i < len(self): raise IndexError
        return self.variables[self.bit.bisect_left(i + 1) - 1]

    def __iter__(self) -> Iterator[KeyT]:
        """
        Iterate over elements in sorted order.

        Time Complexity: O(m log(n + 1)), where m is the number of stored elements and n is the capacity

        Returns:
            Iterator[KeyT]: Iterator over all elements in sorted order
        """
        return iter([self[i] for i in range(len(self))])

    def add(self, v: KeyT) -> bool:
        """
        Add element v to the set.

        Args:
            v (KeyT): Element to add

        Returns:
            bool: True if element was added, False if already present

        Raises:
            KeyError: If v is not in the sorted variables list

        Time Complexity:
            O(log n)
        """
        pos, found = self._findpos(v)
        if not found: raise KeyError('given value is not in sorted variables')
        if v in self: return False
        self.bit.add(pos, 1)
        return True

    def discard(self, v: KeyT) -> bool:
        """
        Remove the specified value if present.

        Args:
            v: Value to remove.

        Returns:
            True if removed, otherwise False.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        pos, found = self._findpos(v)
        if not found:
            return False
        if not self.bit.get(pos):
            return False
        self.bit.add(pos, -1)
        return True

    def remove(self, v: KeyT) -> None:
        """
        Remove the specified value.

        Args:
            v: Value to remove.

        Returns:
            None.

        Raises:
            KeyError: If the value is absent.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if not self.discard(v):
            raise KeyError(v)

    def pop(self, i: int) -> KeyT:
        """
        Remove and return the i-th smallest element.

        Args:
            i (int): Index of element to remove

        Returns:
            KeyT: The removed element

        Raises:
            IndexError: If i is out of range [0, len(self))

        Time Complexity:
            O(log n)
        """
        if not 0 <= i < len(self): raise IndexError
        idx = self.bit.bisect_left(i + 1) - 1
        v = self.variables[idx]
        self.bit.add(idx, -1)
        return v

    def index(self, v: KeyT) -> int:
        """
        Return the first sorted index of ``v``.

        Args:
            v: Search value.

        Returns:
            Zero-based index of the first occurrence.

        Raises:
            ValueError: If the value is absent.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        pos, found = self._findpos(v)
        if not found or self.bit.get(pos) == 0:
            raise ValueError('given value is not contained')
        return self.bit.sum(pos)

    def bisect_left(self, v: KeyT) -> int:
        """
        Return the number of elements strictly less than ``v``.

        Args:
            v: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        pos, _ = self._findpos(v)
        return self.bit.sum(pos)

    def bisect_right(self, v: KeyT) -> int:
        """
        Return the number of elements less than or equal to ``v``.

        Args:
            v: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        pos, found = self._findpos(v)
        return self.bit.sum(pos + found)

    def max(self) -> KeyT:
        """
        Get the maximum element in the set.

        Returns:
            KeyT: Maximum element

        Raises:
            IndexError: If the container is empty.

        Time Complexity:
            O(log n)
        """
        return self[len(self) - 1]

    def min(self) -> KeyT:
        """
        Get the minimum element in the set.

        Returns:
            KeyT: Minimum element

        Raises:
            IndexError: If the container is empty.

        Time Complexity:
            O(log n)
        """
        return self[0]

    def median(self, upper: bool = False) -> KeyT:
        """
        Get the median element in the set.

        Args:
            upper: If True, return the upper median when the size is even.
                   Otherwise, return the lower median.

        Returns:
            KeyT: Median element.

        Raises:
            IndexError: If the set is empty.

        Time Complexity:
            O(log n)
        """
        m = len(self)
        if m == 0: raise IndexError
        return self[m // 2 if upper else (m - 1) // 2]

    def predecessor(self, v: KeyT, inclusive: bool = True) -> KeyT | None:
        """Return the largest stored value less than or equal to ``v``.

        Args:
            v: Search value; it may be absent or outside the registered candidates.
            inclusive: If False, require a value strictly less than v.

        Returns:
            Matching stored value, or None if no such value exists.

        Notes:
            Ordering uses only <. If inclusive is False, all values equivalent
            to the search value under this ordering are skipped.

        Time Complexity:
            O(log n), where n is the number of registered values.

        Space Complexity:
            O(1) auxiliary space.
        """
        pos = bisect_right(self.variables, v) if inclusive else bisect_left(self.variables, v)
        index = self.bit.bisect_left(self.bit.sum(pos)) - 1
        if not 0 <= index < self.n:
            return None
        return self.variables[index]

    def successor(self, v: KeyT, inclusive: bool = True) -> KeyT | None:
        """Return the smallest stored value greater than or equal to ``v``.

        Args:
            v: Search value; it may be absent or outside the registered candidates.
            inclusive: If False, require a value strictly greater than v.

        Returns:
            Matching stored value, or None if no such value exists.

        Notes:
            Ordering uses only <. If inclusive is False, all values equivalent
            to the search value under this ordering are skipped.

        Time Complexity:
            O(log n), where n is the number of registered values.

        Space Complexity:
            O(1) auxiliary space.
        """
        pos = bisect_left(self.variables, v) if inclusive else bisect_right(self.variables, v)
        index = self.bit.bisect_left(self.bit.sum(pos) + 1) - 1
        if not 0 <= index < self.n:
            return None
        return self.variables[index]


class SortedMultisetBIT(Generic[KeyT]):
    """
    Sorted multiset data structure for arbitrary comparable elements using Fenwick Tree.

    Similar to SortedSetBIT but allows multiple copies of the same element.
    Maintains elements in sorted order with support for order statistics and multiplicity.

    Attributes:
        n: Number of possible distinct values (length of variables list)
        variables: Sorted list of possible values that can be stored
        bit: Fenwick Tree to maintain counts of each variable

    Time Complexities:
        - add/discard: O(log n)
        - __contains__: O(log n)
        - __getitem__ (k-th element): O(log n)
        - count: O(log n)
        - index/bisect_left/bisect_right: O(log n)
        - range_count: O(log n)

    Examples:
        >>> # String multiset
        >>> ms = SortedMultisetBIT(['apple', 'banana', 'cherry'])
        >>> ms.add('banana')
        1
        >>> ms.add('banana')  # Add duplicate
        1
        >>> ms.add('apple')
        1
        >>> print(len(ms))  # 3 (total elements)
        3
        >>> print(ms.count('banana'))  # 2 (count of 'banana')
        2
        >>> print(ms[1])  # Second element: 'banana'
        banana
        >>> print(ms.range_count('apple', 'cherry'))  # Count in range
        3

    Notes:
        All possible values must be specified at initialization.
        Supports duplicate elements unlike SortedSetBIT.

    Space Complexity:
        O(n) in the constructor input size or configured capacity

    """
    def __init__(self, variables: list[KeyT]) -> None:
        """
        Initialize the sorted multiset with a list of possible values.

        Args:
            variables (list[KeyT]): A sorted list of possible values that can be stored in the multiset. Must be strictly increasing.

        Raises:
            ValueError: If variables is not strictly increasing under <

        Notes:
            Copies the candidate list. Ordering equivalence uses <, without requiring __eq__.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        if any(not a < b for a, b in zip(variables, variables[1:])):
            raise ValueError('variables must be sorted')
        self.n = len(variables)
        self.variables = variables[:]
        self.bit = FenwickTree(self.n)

    def _findpos(self, v: KeyT) ->tuple[int, bool]:
        """
        Find position of value v in the variables list.

        Time Complexity: O(log n)

        Args:
            v (KeyT): Value to find

        Returns:
            tuple[int, bool]: (position, found) where position is the index
                            and found indicates if the equivalent key under < was found
        """
        p = bisect_left(self.variables, v)
        if p == self.n or v < self.variables[p]: return p, False
        return p, True

    def build(self, arr: Sequence[int]) -> None:
        """
        Build the multiset from an initial array of counts.

        Args:
            arr (Sequence[int]): Array where arr[i] is the count of variables[i]

        Raises:
            ValueError: If the length differs from the variables list or any count is negative.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        if len(arr) != self.n:
            raise ValueError('length of arr must be equal to length of variables')
        if any(count < 0 for count in arr):
            raise ValueError('counts must be nonnegative')
        self.bit.build(arr)

    def __str__(self) -> str:
        """
        Return string representation of the multiset.

        Time Complexity: O(m log(n + 1)), where m is the number of stored elements and n is the capacity

        Returns:
            str: String representation showing all elements in sorted order
        """
        return [self[i] for i in range(len(self))].__str__()

    def __len__(self) -> int:
        """
        Get the total number of elements in the multiset.

        Time Complexity: O(log n)

        Returns:
            int: Total number of elements (including duplicates)
        """
        return self.bit.range_sum(0, self.n)

    def __contains__(self, v: KeyT) -> bool:
        """
        Check if value v exists in the multiset.

        Time Complexity: O(log n)

        Args:
            v (KeyT): Value to check

        Returns:
            bool: True if v exists (count > 0), False otherwise, including values outside the storage domain
        """
        pos, found = self._findpos(v)
        if not found: return False
        return self.bit.get(pos) > 0

    def __getitem__(self, i: int) -> KeyT:
        """
        Get the i-th smallest element in the multiset.

        Time Complexity: O(log n)

        Args:
            i (int): Index (0-based) of element to retrieve

        Returns:
            KeyT: The i-th smallest element (counting duplicates)

        Raises:
            IndexError: If i is out of range [0, len(self))
        """
        if not 0 <= i < len(self): raise IndexError
        return self.variables[self.bit.bisect_left(i + 1) - 1]

    def __iter__(self) -> Iterator[KeyT]:
        """
        Iterate over all elements in sorted order (including duplicates).

        Time Complexity: O(m log(n + 1)), where m is the number of stored elements and n is the capacity

        Returns:
            Iterator[KeyT]: Iterator over all elements
        """
        return iter([self[i] for i in range(len(self))])

    def add(self, v: KeyT, count: int = 1) -> int:
        """
        Add ``count`` copies of the value to the multiset.

        Args:
            v: Value to add, registered at construction when count is positive.
            count: Number of copies to add. Zero is a no-op, even if v is unregistered.

        Returns:
            Number of copies added, equal to ``count``.

        Raises:
            ValueError: If ``count`` is negative. The contents remain unchanged.
            KeyError: If count is positive and v is not in the sorted variables list.

        Time Complexity:
            O(log n), where n is the number of registered values; O(1) if count is zero.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return 0
        pos, found = self._findpos(v)
        if not found: raise KeyError('given value is not in sorted variables')
        self.bit.add(pos, count)
        return count

    def discard(self, v: KeyT, count: int = 1) -> int:
        """
        Remove up to ``count`` copies.

        Args:
            v: Value to remove.
            count: Maximum number of copies to remove. Zero is a no-op.

        Returns:
            Number of copies actually removed; zero if the value is absent.

        Raises:
            ValueError: If ``count`` is negative.

        Notes:
            Values outside the storage range or registered candidates are absent.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return 0
        pos, found = self._findpos(v)
        if not found:
            return 0
        removed = min(count, self.bit.get(pos))
        if removed:
            self.bit.add(pos, -removed)
        return removed

    def remove(self, v: KeyT, count: int = 1, validity_check: bool = True) -> None:
        """
        Remove exactly ``count`` copies.

        Args:
            v: Value to remove.
            count: Number of copies to remove. Zero is a no-op.
            validity_check: If False, the caller guarantees that at least ``count`` copies exist.

        Returns:
            None.

        Raises:
            KeyError: If ``validity_check=True`` and too few copies exist. The contents remain unchanged.
            ValueError: If ``count`` is negative.

        Notes:
            With ``validity_check=False``, the availability lookup is skipped.
            The caller must establish that the requested copies exist.
            Negative counts are rejected in either mode.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return
        pos, found = self._findpos(v)
        if not found or (validity_check and self.bit.get(pos) < count):
            raise KeyError(v)
        self.bit.add(pos, -count)

    def pop(self, i: int) -> KeyT:
        """
        Remove and return the i-th smallest element.

        Args:
            i (int): Index of element to remove

        Returns:
            KeyT: The removed element

        Raises:
            IndexError: If i is out of range [0, len(self))

        Time Complexity:
            O(log n)
        """
        if not 0 <= i < len(self): raise IndexError
        idx = self.bit.bisect_left(i + 1) - 1
        v = self.variables[idx]
        self.bit.add(idx, -1)
        return v

    def count(self, v: KeyT) -> int:
        """
        Get the count of element v in the multiset.

        Args:
            v (KeyT): Element to count

        Returns:
            int: Number of occurrences of v in the multiset

        Time Complexity:
            O(log n)
        """
        pos, found = self._findpos(v)
        if not found: return 0
        return self.bit.get(pos)

    def index(self, v: KeyT) -> int:
        """
        Return the first sorted index of ``v``.

        Args:
            v: Search value.

        Returns:
            Zero-based index of the first occurrence.

        Raises:
            ValueError: If the value is absent.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        pos, found = self._findpos(v)
        if not found or self.bit.get(pos) == 0:
            raise ValueError('given value is not contained')
        return self.bit.sum(pos)

    def bisect_left(self, v: KeyT) -> int:
        """
        Return the number of elements strictly less than ``v``.

        Args:
            v: Search value.

        Returns:
            Insertion index in sorted order, counting each copy separately.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        pos, _ = self._findpos(v)
        return self.bit.sum(pos)

    def bisect_right(self, v: KeyT) -> int:
        """
        Return the number of elements less than or equal to ``v``.

        Args:
            v: Search value.

        Returns:
            Insertion index in sorted order, counting each copy separately.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            O(log n), where n is the configured capacity.
        """
        pos, found = self._findpos(v)
        return self.bit.sum(pos + found)

    def max(self) -> KeyT:
        """
        Get the maximum element in the multiset.

        Returns:
            KeyT: Maximum element

        Raises:
            IndexError: If the container is empty.

        Time Complexity:
            O(log n)
        """
        return self[len(self) - 1]

    def min(self) -> KeyT:
        """
        Get the minimum element in the multiset.

        Returns:
            KeyT: Minimum element

        Raises:
            IndexError: If the container is empty.

        Time Complexity:
            O(log n)
        """
        return self[0]

    def median(self, upper: bool = False) -> KeyT:
        """
        Get the median element in the multiset.

        Args:
            upper: If True, return the upper median when the size is even.
                   Otherwise, return the lower median.

        Returns:
            KeyT: Median element.

        Raises:
            IndexError: If the multiset is empty.

        Time Complexity:
            O(log n)
        """
        m = len(self)
        if m == 0: raise IndexError
        return self[m // 2 if upper else (m - 1) // 2]

    def predecessor(self, v: KeyT, inclusive: bool = True) -> KeyT | None:
        """Return the largest stored value less than or equal to ``v``.

        Args:
            v: Search value; it may be absent or outside the registered candidates.
            inclusive: If False, require a value strictly less than v.

        Returns:
            Matching stored value, or None if no such value exists.

        Notes:
            Ordering uses only <. If inclusive is False, all values equivalent
            to the search value under this ordering are skipped.

        Time Complexity:
            O(log n), where n is the number of registered values.

        Space Complexity:
            O(1) auxiliary space.
        """
        pos = bisect_right(self.variables, v) if inclusive else bisect_left(self.variables, v)
        index = self.bit.bisect_left(self.bit.sum(pos)) - 1
        if not 0 <= index < self.n:
            return None
        return self.variables[index]

    def successor(self, v: KeyT, inclusive: bool = True) -> KeyT | None:
        """Return the smallest stored value greater than or equal to ``v``.

        Args:
            v: Search value; it may be absent or outside the registered candidates.
            inclusive: If False, require a value strictly greater than v.

        Returns:
            Matching stored value, or None if no such value exists.

        Notes:
            Ordering uses only <. If inclusive is False, all values equivalent
            to the search value under this ordering are skipped.

        Time Complexity:
            O(log n), where n is the number of registered values.

        Space Complexity:
            O(1) auxiliary space.
        """
        pos = bisect_left(self.variables, v) if inclusive else bisect_right(self.variables, v)
        index = self.bit.bisect_left(self.bit.sum(pos) + 1) - 1
        if not 0 <= index < self.n:
            return None
        return self.variables[index]

    def range_count(self, l: KeyT, r: KeyT) -> int:
        """
        Count elements in the range [l, r).

        Args:
            l (KeyT): Left boundary (inclusive)
            r (KeyT): Right boundary (exclusive)

        Returns:
            int: Number of elements in range [l, r)

        Raises:
            KeyError: If l or r is not in the sorted variables list

        Time Complexity:
            O(log n)
        """
        posl, foundl = self._findpos(l)
        posr, foundr = self._findpos(r)
        if not foundl: raise KeyError('left value is not in sorted variables')
        if not foundr: raise KeyError('right value is not in sorted variables')
        return self.bit.range_sum(posl, posr)
