#!/usr/bin/env python3

from __future__ import annotations
from typing import Generic, cast
from collections.abc import Sequence, Callable

from cplib.datastructure.dsu import PartiallyPersistentDSU as PartiallyPersistentDSU
from cplib.tools.type import T, ValueT, ActionT


class PartiallyPersistentArray(Generic[T]):
    """Partially persistent array with efficient version management.

    A data structure that maintains historical versions of an array,
    allowing queries to past states. Updates create new versions,
    but only the most recent version can be modified (partial persistence).

    Time Complexities:
        - set: O(1) amortized
        - get: O(log k) where k is the number of updates to position i
        - update: O(1)
        - build: O(n)

    Args:
        n: Size of the array
        auto_update: If True, automatically increments version on each set
        init_val: Initial value for all elements (optional)

    Examples:
        >>> arr = PartiallyPersistentArray(5)
        >>> arr.build([1, 2, 3, 4, 5])
        >>> arr.set(2, 10)  # Write version 0, then advance the active timestamp to 1.
        1
        >>> arr.get(2, 0)   # Get position 2 at version 0
        10
        >>> arr.set(2, 20)  # Write version 1, then advance to 2.
        2
        >>> arr.get(2, 1)   # Get position 2 at version 1
        20
        >>> arr.get(2, 0)   # Still can access version 0
        10

    Notes:
        Version -1 is the initial state. After build, last=0 is the active
        timestamp. With auto_update=True, set writes at the current timestamp
        and returns the next timestamp. Query the previous timestamp to read
        the newly frozen state.

    Space Complexity:
        O(n + q), where q is the number of recorded point updates.

    Value Ownership:
        Stored values are not deep-copied. Do not mutate values shared by versions.
    """
    def __init__(self, n: int, auto_update: bool = True, init_val: T | None = None) -> None:
        """Initialize a PartiallyPersistentArray.

        Args:
            n (int): Size of the array.
            auto_update (bool, optional): Whether to automatically update the timestamp. Defaults to True.
            init_val (Optional[T], optional): Initial value for all elements. If specified, will call `build`. Defaults to None.

        Time Complexity:
            O(n)

        Raises:
            ValueError: If n is negative.

        Notes:
            init_val=None leaves the array unbuilt. To store None as a value,
            call build explicitly with a sequence containing None.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.auto_update = auto_update
        self.last = -1
        self.built = False
        self.data: list[list[T]] = [[] for _ in range(n)]
        self.time: list[list[int]] = [[] for _ in range(n)]
        if init_val is not None:
            self.build([init_val] * n)

    def build(self, arr: Sequence[T]) -> None:
        """Build the partial persistent array using the provided sequence.

        Args:
            arr (Sequence[T]): Initial sequence to build the array.

        Raises:
            AssertionError: If the array is already built or the provided sequence does not match the specified size.

        Time Complexity:
            O(n)

        Returns:
            None.
        """
        assert not self.built and len(arr) == self.n
        self.built = True
        for i, a in enumerate(arr):
            self.data[i].append(a)
            self.time[i].append(-1)
        self.update()

    def set(self, i: int, x: T) -> int:
        """Set the value at the specified index.

        If `auto_update` is True, this creates a new version of the array.
        Otherwise, the active timestamp stays unchanged. Repeated writes to
        the same position in that timestamp replace its pending value.

        Args:
            i (int): Index to set the value at.
            x (T): Value to set.

        Returns:
            int: The active timestamp after the call. With auto_update=True,
                the update was recorded at the returned timestamp minus one.

        Raises:
            AssertionError: If unbuilt or i is outside [0, n).

        Time Complexity:
            O(1) amortized.
        """
        assert self.built
        assert 0 <= i < self.n
        if self.time[i][-1] == self.last:
            self.data[i][-1] = x
        else:
            self.data[i].append(x)
            self.time[i].append(self.last)
        if self.auto_update:
            self.update()
        return self.last

    def get(self, i: int, t: int) -> T:
        """Get the value at the specified index from a specified version of the array.

        Args:
            i (int): Index to retrieve the value from.
            t (int): Version (timestamp) of the array to get the value from.

        Returns:
            T: The value at the specified index from the specified version.

        Raises:
            AssertionError: If unbuilt, i is outside [0, n), or t is outside [-1, last].

        Time Complexity:
            O(log(k + 1)), where k is the number of recorded updates at index i.
        """
        assert self.built
        assert 0 <= i < self.n
        assert -1 <= t <= self.last
        lo, hi = 0, len(self.time[i])
        while hi - lo > 1:
            mid = (hi + lo) // 2
            if self.time[i][mid] <= t:
                lo = mid
            else:
                hi = mid
        return self.data[i][lo]

    def update(self) -> int:
        """
        Update the version (timestamp) of the array.

        Returns:
            int: The updated version (timestamp).

        Raises:
            AssertionError: If the array is not built.

        Time Complexity:
            O(1)
        """
        assert self.built
        self.last += 1
        return self.last


class FullyPersistentArray(Generic[T]):
    """Fully persistent array supporting updates to any version.

    A persistent data structure that allows both queries and updates
    to any historical version, creating a branching version tree.
    Uses path copying with a tree structure for efficiency.

    Time Complexities:
        - set: O(log n)
        - get: O(log n)
        - update: O(1)
        - build: O(n)

    Args:
        n: Size of the array
        child_num: Branching factor of internal tree (default: 64)
        auto_update: If True, automatically increments version on each set
        init_val: Initial value for all elements (optional)

    Examples:
        >>> arr = FullyPersistentArray(5)
        >>> arr.build([1, 2, 3, 4, 5])
        >>> arr.set(2, 10, -1)  # Write version 0, then return the next active timestamp.
        1
        >>> arr.set(3, 15, -1)  # Write version 1, branching from the initial state.
        2
        >>> arr.get(2, 0)      # Version 0 has modified position 2
        10
        >>> arr.get(3, 0)      # But position 3 unchanged in version 0
        4
        >>> arr.get(3, 1)      # Version 1 has modified position 3
        15

    Notes:
        Unlike partial persistence, any version can be modified,
        creating a new branch in the version tree. Version -1 is the initial
        state. Updates write the active version last; automatic advancement
        then returns the next active timestamp, not the frozen version number.

    Space Complexity:
        O(P + q * B * (1 + log_B(n + 1)) + v), where B=child_num,
        P=B**ceil(log_B(max(1, n))), q is the number of point updates,
        and v is the number of timestamp advancements. For fixed B,
        this is O(n + q * (1 + log(n + 1)) + v + 1).

    Value Ownership:
        Stored values are not deep-copied. Do not mutate values shared by versions.

    Version Contract:
        Version -1 is the initial state. last is a mutable working version.
        Updates replace last using the explicitly selected base version.
        update freezes it and creates the next working version with the same
        contents. Automatic updates return that next working timestamp.
        Valid query/base timestamps are -1 through last, inclusive.
    """
    def __init__(self, n: int, child_num: int = 64, auto_update: bool = True, init_val: T | None = None) -> None:
        """Initialize a FullyPersistentArray.

        Args:
            n (int): Size of the array.
            child_num (int, optional): Maximum number of children in the tree representation. Defaults to 64.
            auto_update (bool, optional): Whether to automatically update the timestamp. Defaults to True.
            init_val (Optional[T], optional): Initial value for all elements. If specified, will call `build`. Defaults to None.

        Time Complexity:
            O(1 + log_B(n + 1)) without init_val, where B=child_num;
            O(P) with initialization, where P=B**ceil(log_B(max(1, n))).

        Raises:
            ValueError: If n is negative.
            ValueError: If child_num is less than 2.

        Notes:
            init_val=None leaves the array unbuilt. To store None as a value,
            call build explicitly with a sequence containing None.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        if child_num < 2:
            raise ValueError('child_num must be at least 2')
        self.child_num = child_num
        self.auto_update = auto_update
        self.built = False
        self.data: list[T | None] = []
        self.childs: list[list[int] | None] = []
        self.last = -1
        self.dep = 0
        self.ofs = 0
        while n > 1:
            n = (n + self.child_num - 1) // self.child_num
            self.ofs += self.child_num ** self.dep
            self.dep += 1
        self.roots: list[int] = []
        if init_val is not None:
            self.build([init_val] * self.n)

    def build(self, arr: Sequence[T]) -> None:
        """Build the fully persistent array using the provided sequence.

        Args:
            arr (Sequence[T]): Initial sequence to build the array.

        Raises:
            AssertionError: If the array is already built or the provided sequence does not match the specified size.

        Time Complexity:
            O(P), where P=child_num**ceil(log_{child_num}(max(1, n))).

        Returns:
            None.
        """
        assert not self.built and len(arr) == self.n
        self.built = True
        self.roots.append(0)
        ofs = 0
        for d in range(self.dep):
            nofs = ofs + self.child_num ** d
            for v in range(ofs, nofs):
                self.data.append(None)
                self.childs.append(list(range(v * self.child_num + 1, (v + 1) * self.child_num + 1)))
            ofs = nofs
        self.data.extend(list(arr) + [None] * (self.child_num ** self.dep - self.n))
        self.childs.extend([None] * (self.child_num ** self.dep))
        self.update()

    def get(self, i: int, t: int) -> T:
        """Get the value at the specified index from a specified version of the array.

        Args:
            i (int): Index to retrieve the value from.
            t (int): Version (timestamp) of the array to get the value from.

        Returns:
            T: The value at the specified index from the specified version.

        Raises:
            AssertionError: If the array is not built or index/time is out of bounds.

        Time Complexity:
            O(1 + log_{child_num}(n + 1))
        """
        assert self.built
        assert 0 <= i < self.n
        assert -1 <= t <= self.last
        v = self.roots[t + 1]
        cur = i + self.ofs
        order: list[int] = []
        for _ in range(self.dep):
            cur, c = divmod((cur - 1), self.child_num)
            order.append(c)
        for c in order[::-1]:
            childs = self.childs[v]
            assert childs is not None
            v = childs[c]
        # A validated index always reaches a value leaf, including a stored None.
        return cast(T, self.data[v])

    def set(self, i: int, x: T, t: int) -> int:
        """
        Set the value at the specified index for a specified version.

        If `auto_update` is True, this creates a new version of the array.
        Otherwise, the active timestamp stays unchanged. Each call replaces
        the active branch with a modified copy of version t. Use t=last to
        accumulate several edits in the active branch.

        Args:
            i (int): Index to set the value at.
            x (T): Value to set.
            t (int): Version (timestamp) to set the value for.

        Returns:
            int: The active timestamp after the call. With auto_update=True,
                the newly frozen version is the returned timestamp minus one.

        Raises:
            AssertionError: If the array is not built or index/time is out of bounds.

        Time Complexity:
            O(child_num * log_{child_num}(n + 1)) for copying child arrays.
        """
        assert self.built
        assert 0 <= i < self.n
        assert -1 <= t <= self.last
        pv = self.roots[t + 1]
        nv = len(self.data)
        self.roots[self.last + 1] = nv
        cur = i + self.ofs
        order: list[int] = []
        for _ in range(self.dep):
            cur, c = divmod((cur - 1), self.child_num)
            order.append(c)
        for c in order[::-1]:
            self.data.append(None)
            pv_childs = self.childs[pv]
            assert pv_childs is not None
            self.childs.append(pv_childs[:])
            nv_childs = self.childs[nv]
            assert nv_childs is not None
            nv_childs[c] = nv = len(self.data)
            pv = pv_childs[c]
        self.data.append(x)
        self.childs.append(None)
        if self.auto_update:
            self.update()
        return self.last

    def update(self) -> int:
        """Update the version (timestamp) of the array.

        Returns:
            int: The updated version (timestamp).

        Raises:
            AssertionError: If the array is not built.

        Time Complexity:
            O(1) amortized
        """
        assert self.built
        self.roots.append(self.roots[-1])
        self.last += 1
        return self.last


class FullyPersistentDSU:
    """Fully persistent disjoint set union (Union-Find) data structure.

    Maintains a collection of disjoint sets with merge operations,
    supporting queries and modifications to any historical version.
    Uses union by size for efficiency.

    Time Complexities:
        - leader: O(log^2 n)
        - merge: O(log^2 n)
        - update: O(1)

    Args:
        n: Number of elements (0 to n-1)
        auto_update: If True, automatically increments version on each merge

    Examples:
        >>> dsu = FullyPersistentDSU(5)
        >>> dsu.merge(0, 1, -1)  # Merge 0 and 1 at version -1
        (True, 1)
        >>> dsu.merge(2, 3, 0)   # Merge 2 and 3 at version 0
        (True, 2)
        >>> dsu.leader(1, 0)     # Find leader of 1 at version 0
        0
        >>> dsu.leader(2, 0)     # 2 not merged yet at version 0
        2
        >>> dsu.leader(2, 1)     # 2 is merged at version 1
        2
        >>> dsu.merge(0, 2, 1)   # Connect components
        (True, 3)

    Notes:
        Returns (success, next_timestamp) with automatic advancement enabled.
        The newly frozen version is next_timestamp - 1. Success is False if
        the elements were already in the same set in the requested version.

    Space Complexity:
        O(n + q * (1 + log(n + 1)) + v + 1), where q counts merge attempts
        and v counts timestamp advancements, including explicit update calls.

    Value Ownership:
        Stored values are not deep-copied. Do not mutate values shared by versions.

    Version Contract:
        Version -1 is the initial state. last is a mutable working version.
        Updates replace last using the explicitly selected base version.
        update freezes it and creates the next working version with the same
        contents. Automatic updates return that next working timestamp.
        Valid query/base timestamps are -1 through last, inclusive.
    """
    def __init__(self, n: int, auto_update: bool = True) -> None:
        """Initialize a fully persistent disjoint set union (DSU) data structure.

        Args:
            n (int): Number of elements.
            auto_update (bool): If set to True, creates a new DSU version automatically after every merge.
                                Default is True.

        Time Complexity:
            O(n)

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.par_size = FullyPersistentArray(n, child_num=64, auto_update=False, init_val=-1)
        self.auto_update = auto_update
        self.last = 0

    def leader(self, x: int, t: int) -> int:
        """Find the representative (leader) of element x at version t.

        Args:
            x (int): The element to find its root.
            t (int): The version to check.

        Returns:
            int: The leader of the element x at version t.

        Time Complexity:
            O(log^2 n)

        Raises:
            AssertionError: If an element or timestamp is outside its valid range.
        """
        v = x
        while True:
            nv = self.par_size.get(v, t)
            if nv < 0: return v
            v = nv

    def merge(self, x: int, y: int, t: int) -> tuple[bool, int]:
        """Merge the sets containing elements x and y.

        Args:
            x (int): One element.
            y (int): Another element.
            t (int): The version to merge.

        Returns:
            tuple[bool, int]: A tuple containing:
                              - True if the merge was successful (i.e., x and y were not already in the same set),
                                False otherwise.
                              - The active timestamp after the call. With auto_update=True,
                                the resulting branch is stored at this timestamp minus one,
                                including when success is False.

        Time Complexity:
            O(log^2 n)

        Raises:
            AssertionError: If an element or timestamp is outside its valid range.

        Notes:
            Even when the elements are already connected, the resulting working
            branch is based on t, not on the previous working branch.
        """
        x = self.leader(x, t)
        y = self.leader(y, t)
        if x == y:
            self.par_size.roots[self.last + 1] = self.par_size.roots[t + 1]
            if self.auto_update:
                self.last = self.update()
            return False, self.last
        px = self.par_size.get(x, t)
        py = self.par_size.get(y, t)
        if px > py:
            x, y = y, x
            px, py = py, px
        t = self.par_size.set(x, px + py, t)
        self.par_size.set(y, x, t)
        if self.auto_update:
            self.last = self.update()
        return True, self.last

    def update(self) -> int:
        """Create a new version of the DSU.

        Returns:
            int: The new version number.

        Time Complexity:
            O(1) amortized
        """
        self.last = self.par_size.update()
        return self.last


class FullyPersistentSegmentTree(Generic[ValueT]):
    """Fully persistent segment tree without lazy propagation.

    A persistent data structure supporting point updates and range queries
    on any historical version. Simpler and faster than the lazy version
    when range updates are not needed.

    Time Complexities:
        - build: O(n)
        - set: O(log n)
        - get: O(log n)
        - prod: O(log n)
        - update: O(1)

    Args:
        n: Number of elements
        op: Binary operation for combining values (associative)
        e: Identity element for op
        auto_update: If True, automatically increments version

    Examples:
        >>> # Range sum example
        >>> seg = FullyPersistentSegmentTree(5, lambda x, y: x + y, 0)
        >>> seg.build([1, 2, 3, 4, 5])
        >>> seg.prod(1, 4, -1)    # Sum of [2,3,4] at initial version
        9
        >>> seg.set(2, 10, -1)    # Write version 0 and advance to timestamp 1.
        1
        >>> seg.prod(1, 4, 0)     # Sum after update
        16
        >>> seg.get(2, -1)        # Original value
        3
        >>> seg.get(2, 0)         # Updated value
        10

    Notes:
        Version -1 refers to the initial state after build(). Updates write
        the active version last. With auto_update=True, the returned timestamp
        is one greater than the newly frozen version number.
        Unlike the lazy version, this only supports point updates,
        not range updates. Use FullyPersistentLazySegmentTree for
        range update operations.

    Space Complexity:
        O(n + q * (1 + log(n + 1)) + v + 1), where q counts point updates
        and v counts timestamp advancements, including explicit update calls.

    Value Ownership:
        Stored values are not deep-copied. Do not mutate values shared by versions.

    Version Contract:
        Version -1 is the initial state. last is a mutable working version.
        Updates replace last using the explicitly selected base version.
        update freezes it and creates the next working version with the same
        contents. Automatic updates return that next working timestamp.
        Valid query/base timestamps are -1 through last, inclusive.

    Callback Contract:
        op is associative with identity e and need not be commutative.
        It must not mutate its arguments. Bounds assume O(1) callback cost
        and fixed-size values.
    """
    def __init__(self, n: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, auto_update: bool = True) -> None:
        """Initialize an empty fully persistent segment tree.

        Args:
            n: Number of elements.
            op: Associative operation for range products.
            e: Identity element for ``op``.
            auto_update: If True, automatically advances the timestamp after updates.

        Time Complexity:
            O(1); build allocates the tree.

        Raises:
            ValueError: If n is negative.

        Returns:
            None.
        """
        if n < 0:
            raise ValueError('n must be nonnegative')
        self.n = n
        self.op = op
        self.e = e
        self.auto_update = auto_update
        self.log = max(0, n - 1).bit_length()
        self.size = 1 << self.log
        self.built = False
        self.last = -1
        self.roots: list[int] = []
        self.data: list[ValueT] = []
        self.lt: list[int] = []
        self.rt: list[int] = []

    def _allocate_node(self, data: ValueT, left: int, right: int) -> int:
        """Allocate a new node and return its index."""
        idx = len(self.data)
        self.data.append(data)
        self.lt.append(left)
        self.rt.append(right)
        return idx

    def _update_node(self, left: int, right: int) -> int:
        """Update a node based on its children and return new node index."""
        left_data = self.data[left] if left != -1 else self.e
        right_data = self.data[right] if right != -1 else self.e
        return self._allocate_node(self.op(left_data, right_data), left, right)

    def build(self, arr: Sequence[ValueT]) -> None:
        """Build the fully persistent segment tree from a sequence.

        Args:
            arr (Sequence[ValueT]): Initial sequence to build the tree.

        Raises:
            AssertionError: If already built or len(arr) differs from n.

        Time Complexity:
            O(n)

        Returns:
            None.
        """
        assert not self.built and len(arr) == self.n
        self.built = True
        nodes = [-1] * (2 * self.size)
        for i in range(len(arr)):
            nodes[self.size + i] = self._allocate_node(arr[i], -1, -1)
        for i in range(self.size - 1, 0, -1):
            left = nodes[2 * i]
            right = nodes[2 * i + 1]
            if left != -1 or right != -1:
                nodes[i] = self._update_node(left, right)
        self.roots.append(nodes[1])
        self.update()

    def set(self, p: int, x: ValueT, t: int) -> int:
        """
        Set the value at position p to x at time t.

        Args:
            p (int): Position to update (0-indexed).
            x (ValueT): New value.
            t (int): Version to base the update on.

        Returns:
            int: The active timestamp after the call. With auto_update=True,
                the newly frozen version is the returned timestamp minus one.

        Raises:
            AssertionError: If build has not been called, or any of ``0 <= p < n``, ``-1 <= t <= last`` is false.

        Time Complexity:
            O(log n)
        """
        assert self.built
        assert 0 <= p < self.n
        assert -1 <= t <= self.last
        root = self.roots[t + 1]
        path: list[tuple[int, int, int]] = []
        node = root
        l, r = 0, self.size
        while r - l > 1:
            path.append((node, l, r))
            mid = (l + r) // 2
            if p < mid:
                node = self.lt[node] if node != -1 else -1
                r = mid
            else:
                node = self.rt[node] if node != -1 else -1
                l = mid
        new_node = self._allocate_node(x, -1, -1)
        for path_node, path_l, path_r in reversed(path):
            mid = (path_l + path_r) // 2
            if p < mid:
                right_child = self.rt[path_node] if path_node != -1 else -1
                new_node = self._update_node(new_node, right_child)
            else:
                left_child = self.lt[path_node] if path_node != -1 else -1
                new_node = self._update_node(left_child, new_node)
        self.roots[self.last + 1] = new_node
        if self.auto_update:
            self.update()
        return self.last

    def get(self, p: int, t: int) -> ValueT:
        """
        Get the value at position p at time t.

        Args:
            p (int): Position to query (0-indexed).
            t (int): Version to query.

        Returns:
            ValueT: Value at position p in version t.

        Raises:
            AssertionError: If build has not been called, or any of ``0 <= p < n``, ``-1 <= t <= last`` is false.

        Time Complexity:
            O(log n)
        """
        assert self.built
        assert 0 <= p < self.n
        assert -1 <= t <= self.last
        node = self.roots[t + 1]
        l, r = 0, self.size
        while r - l > 1:
            if node == -1:
                return self.e
            mid = (l + r) // 2
            if p < mid:
                node = self.lt[node]
                r = mid
            else:
                node = self.rt[node]
                l = mid
        return self.data[node] if node != -1 else self.e

    def prod(self, l: int, r: int, t: int) -> ValueT:
        """
        Compute the product in range [l, r) at time t.

        Args:
            l (int): Left boundary (inclusive).
            r (int): Right boundary (exclusive).
            t (int): Version to query.

        Returns:
            ValueT: Result of the binary operation over the segment.

        Raises:
            AssertionError: If build has not been called, or any of ``0 <= l <= r <= n``, ``-1 <= t <= last`` is false.

        Time Complexity:
            O(log n)
        """
        assert self.built
        assert 0 <= l <= r <= self.n
        assert -1 <= t <= self.last
        if l == r:
            return self.e
        root = self.roots[t + 1]
        stack: list[tuple[int, int, int]] = [(root, 0, self.size)]
        result = self.e
        while stack:
            node, sl, sr = stack.pop()
            if r <= sl or sr <= l or node == -1:
                continue
            if l <= sl and sr <= r:
                result = self.op(result, self.data[node])
            else:
                mid = (sl + sr) // 2
                stack.append((self.rt[node], mid, sr))
                stack.append((self.lt[node], sl, mid))
        return result

    def update(self) -> int:
        """Update the version (timestamp) of the tree.

        Returns:
            int: The updated version (timestamp).

        Raises:
            AssertionError: If build has not been called.

        Time Complexity:
            O(1) amortized
        """
        assert self.built
        self.roots.append(self.roots[-1])
        self.last += 1
        return self.last


class FullyPersistentLazySegmentTree(Generic[ValueT, ActionT]):
    """Fully persistent segment tree with lazy propagation.

    A persistent data structure supporting range updates and range queries
    on any historical version. Combines segment tree efficiency with
    full persistence through path copying.

    Time Complexities:
        - build: O(n)
        - range_apply: O(log n)
        - prod: O(log n)
        - range_copy: O(log n)
        - update: O(1)

    Args:
        n: Number of elements
        op: Binary operation for combining values (associative)
        e: Identity element for op
        mapping: Function to apply updates to values
        composition: Function to compose multiple updates
        id: Identity element for updates
        auto_update: If True, automatically increments version

    Examples:
        >>> # Range sum with range add
        >>> # Each aggregate stores (sum, length), so mapping scales the addition.
        >>> def op(x, y): return (x[0] + y[0], x[1] + y[1])
        >>> def mapping(f, x): return (x[0] + f * x[1], x[1])
        >>> def composition(f, g): return f + g
        >>> seg = FullyPersistentLazySegmentTree(5, op, (0, 0), mapping, composition, 0)
        >>> seg.build([(x, 1) for x in [1, 2, 3, 4, 5]])
        >>> seg.prod(1, 4, -1)[0]    # Sum of [2,3,4] at version -1
        9
        >>> seg.range_apply(1, 4, 10, -1)  # Write version 0, then advance.
        1
        >>> seg.prod(1, 4, 0)[0]     # Sum after update
        39
        >>> seg.range_copy(2, 4, 0, -1)  # Write version 1, restoring positions 2 and 3.
        2
        >>> seg.prod(1, 4, 1)[0]     # Mixed state
        19

    Notes:
        Version -1 is the initial state. Updates write the active version last;
        automatic advancement returns the next timestamp. Mapping must act on
        an aggregate, not just one element, and distribute over op. Composition
        (f, g) must represent applying g first, then f.

    Space Complexity:
        O(n + q * (1 + log(n + 1)) + v + 1), where q counts range updates
        and copies and v counts timestamp advancements. Queries do not
        allocate or mutate tree nodes.

    Value Ownership:
        Stored values are not deep-copied. Do not mutate values shared by versions.

    Version Contract:
        Version -1 is the initial state. last is a mutable working version.
        Updates replace last using the explicitly selected base version.
        update freezes it and creates the next working version with the same
        contents. Automatic updates return that next working timestamp.
        Valid query/base timestamps are -1 through last, inclusive.

    Callback Contract:
        op is associative with identity e and need not be commutative.
        mapping(f, e) must equal e, and mapping distributes over op.
        composition(f, g) applies g first, then f. id leaves values unchanged.
        Callbacks must not mutate their inputs. Bounds assume O(1) callbacks
        and fixed-size values.
    """
    def __init__(self, n: int, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[[ActionT, ValueT], ValueT], composition: Callable[[ActionT, ActionT], ActionT], id: ActionT, auto_update: bool = True) -> None:
        """Initialize a fully persistent lazy segment tree.

        Args:
            n (int): Number of elements in the segment tree.
            op (Callable[[ValueT, ValueT], ValueT]): Binary operation used to combine elements.
            e (ValueT): Identity element for the binary operation `op`.
            mapping (Callable[[ActionT, ValueT], ValueT]): Mapping function to apply updates.
            composition (Callable[[ActionT, ActionT], ActionT]): Composition function for multiple updates.
            id (ActionT): Identity element for updates.
            auto_update (bool, optional): Whether to automatically update the timestamp. Defaults to True.

        Time Complexity:
            O(1); build allocates the tree.

        Raises:
            ValueError: If n is negative.

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
        self.auto_update = auto_update
        self.log = max(0, n - 1).bit_length()
        self.size = 1 << self.log
        self.built = False
        self.last = -1
        self.roots: list[int] = []
        self.data: list[ValueT] = []
        self.lazy: list[ActionT] = []
        self.lt: list[int] = []
        self.rt: list[int] = []

    def _allocate_node(self, data: ValueT, lazy: ActionT, left: int, right: int) -> int:
        """Allocate a new node and return its index."""
        idx = len(self.data)
        self.data.append(data)
        self.lazy.append(lazy)
        self.lt.append(left)
        self.rt.append(right)
        return idx

    def _update(self, left: int, right: int) -> int:
        """Update a node based on its children and return new node index."""
        left_data = self.data[left] if left != -1 else self.e
        right_data = self.data[right] if right != -1 else self.e
        return self._allocate_node(self.op(left_data, right_data), self.id, left, right)

    def _all_apply(self, node: int, f: ActionT, length: int) -> int:
        """Apply lazy value to a node and return new node index."""
        if node == -1:
            if f == self.id:
                return -1
            return self._allocate_node(self.mapping(f, self.e), f, -1, -1)
        new_data = self.mapping(f, self.data[node])
        new_lazy = self.composition(f, self.lazy[node])
        return self._allocate_node(new_data, new_lazy, self.lt[node], self.rt[node])

    def _push(self, node: int, length: int) -> tuple[int, int]:
        """Push lazy value to children and return new left and right indices."""
        if node == -1:
            return -1, -1
        if self.lazy[node] == self.id:
            return self.lt[node], self.rt[node]
        half_len = length // 2
        new_left = self._all_apply(self.lt[node], self.lazy[node], half_len)
        new_right = self._all_apply(self.rt[node], self.lazy[node], half_len)
        return new_left, new_right

    def build(self, arr: Sequence[ValueT]) -> None:
        """Build the fully persistent lazy segment tree from a sequence.

        Args:
            arr (Sequence[ValueT]): Initial sequence to build the tree.

        Raises:
            AssertionError: If already built or len(arr) differs from n.

        Time Complexity:
            O(n)

        Returns:
            None.
        """
        assert not self.built and len(arr) == self.n
        self.built = True
        nodes = [-1] * (2 * self.size)
        for i in range(len(arr)):
            nodes[self.size + i] = self._allocate_node(arr[i], self.id, -1, -1)
        for i in range(self.size - 1, 0, -1):
            left = nodes[2 * i]
            right = nodes[2 * i + 1]
            if left != -1 or right != -1:
                nodes[i] = self._update(left, right)
        self.roots.append(nodes[1])
        self.update()

    def range_apply(self, l: int, r: int, f: ActionT, t: int) -> int:
        """
        Apply an update to range [l, r) at time t.

        Args:
            l (int): Left boundary (inclusive).
            r (int): Right boundary (exclusive).
            f (ActionT): Update to apply.
            t (int): Version to apply the update to.

        Returns:
            int: The active timestamp after the call. With auto_update=True,
                the newly frozen version is the returned timestamp minus one.

        Raises:
            AssertionError: If build has not been called, or any of ``0 <= l <= r <= n``, ``-1 <= t <= last`` is false.

        Time Complexity:
            O(log n)
        """
        assert self.built
        assert 0 <= l <= r <= self.n
        assert -1 <= t <= self.last
        if l == r:
            self.roots[self.last + 1] = self.roots[t + 1]
            if self.auto_update:
                self.update()
            return self.last
        root = self.roots[t + 1]
        stack: list[tuple[int, int, int, int]] = [(root, 0, self.size, 0)]
        result_stack: list[int] = []
        while stack:
            node, sl, sr, phase = stack.pop()
            if phase == 0:
                if r <= sl or sr <= l:
                    result_stack.append(node)
                elif l <= sl and sr <= r:
                    result_stack.append(self._all_apply(node, f, sr - sl))
                else:
                    mid = (sl + sr) // 2
                    new_left, new_right = self._push(node, sr - sl)
                    stack.append((node, sl, sr, 1))
                    stack.append((new_right, mid, sr, 0))
                    stack.append((new_left, sl, mid, 0))
            else:
                right = result_stack.pop()
                left = result_stack.pop()
                result_stack.append(self._update(left, right))
        self.roots[self.last + 1] = result_stack[0]
        if self.auto_update:
            self.update()
        return self.last

    def prod(self, l: int, r: int, t: int) -> ValueT:
        """Compute the product in range [l, r) at time t.

        Args:
            l (int): Left boundary (inclusive).
            r (int): Right boundary (exclusive).
            t (int): Version to query.

        Returns:
            ValueT: Result of the binary operation over the segment.

        Raises:
            AssertionError: If build has not been called, or any of ``0 <= l <= r <= n``, ``-1 <= t <= last`` is false.

        Time Complexity:
            O(log n)

        Space Complexity:
            O(log(n + 1)) auxiliary stack space; no tree nodes are allocated.
        """
        assert self.built
        assert 0 <= l <= r <= self.n
        assert -1 <= t <= self.last
        if l == r:
            return self.e
        root = self.roots[t + 1]
        stack: list[tuple[int, int, int, ActionT]] = [(root, 0, self.size, self.id)]
        result = self.e
        while stack:
            node, sl, sr, pending = stack.pop()
            if r <= sl or sr <= l or node == -1:
                continue
            if l <= sl and sr <= r:
                value = self.data[node] if pending == self.id else self.mapping(pending, self.data[node])
                result = self.op(result, value)
            else:
                mid = (sl + sr) // 2
                pending = self.composition(pending, self.lazy[node])
                stack.append((self.rt[node], mid, sr, pending))
                stack.append((self.lt[node], sl, mid, pending))
        return result

    def range_copy(self, l: int, r: int, k: int, s: int) -> int:
        """
        Create a branch based on version k with [l, r) copied from version s.

        The result is written to the active timestamp last; frozen versions
        k and s are not modified.

        Args:
            l (int): Left boundary (inclusive).
            r (int): Right boundary (exclusive).
            k (int): Target version.
            s (int): Source version.

        Returns:
            int: The active timestamp after the call. With auto_update=True,
                the newly frozen version is the returned timestamp minus one.

        Raises:
            AssertionError: If build has not been called, or any of ``0 <= l <= r <= n``, ``-1 <= k <= last``, ``-1 <= s <= last`` is false.

        Time Complexity:
            O(log(n + 1)), assuming O(1) aggregate and tag operations.
        """
        assert self.built
        assert 0 <= l <= r <= self.n
        assert -1 <= k <= self.last
        assert -1 <= s <= self.last
        if l == r:
            self.roots[self.last + 1] = self.roots[k + 1]
            if self.auto_update:
                self.update()
            return self.last
        target_root = self.roots[k + 1]
        source_root = self.roots[s + 1]
        stack: list[tuple[int, int, int, int, int]] = [(target_root, source_root, 0, self.size, 0)]
        result_stack: list[int] = []
        while stack:
            target_node, source_node, sl, sr, phase = stack.pop()
            if phase == 0:
                if r <= sl or sr <= l:
                    result_stack.append(target_node)
                elif l <= sl and sr <= r:
                    result_stack.append(source_node)
                else:
                    mid = (sl + sr) // 2
                    target_left, target_right = self._push(target_node, sr - sl) if target_node != -1 else (-1, -1)
                    source_left, source_right = self._push(source_node, sr - sl) if source_node != -1 else (-1, -1)
                    stack.append((target_node, source_node, sl, sr, 1))
                    stack.append((target_right, source_right, mid, sr, 0))
                    stack.append((target_left, source_left, sl, mid, 0))
            else:
                right = result_stack.pop()
                left = result_stack.pop()
                result_stack.append(self._update(left, right))
        self.roots[self.last + 1] = result_stack[0]
        if self.auto_update:
            self.update()
        return self.last

    def update(self) -> int:
        """Update the version (timestamp) of the tree.

        Returns:
            int: The updated version (timestamp).

        Raises:
            AssertionError: If build has not been called.

        Time Complexity:
            O(1) amortized
        """
        assert self.built
        self.roots.append(self.roots[-1])
        self.last += 1
        return self.last
