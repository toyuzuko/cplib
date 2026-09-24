#!/usr/bin/env python3

from typing import Generic
from collections.abc import Iterator, Callable
from cplib.tools.type import KeyT, ValueT, ActionT


class ImplicitTreap(Generic[ValueT, ActionT]):
    """
    Implicit Treap with lazy propagation for sequence operations.

    A Treap (tree + heap) is a randomized binary search tree that uses random
    priorities to maintain balance. This implicit version doesn't store keys
    explicitly but uses positions as implicit keys, making it suitable for
    sequence operations.

    Time Complexities:
        - insert/erase: O(log n) expected
        - get/prod: O(log n) expected
        - reverse/range_apply: O(log n) expected
        - build: O(n)

    Type Parameters:
        ValueT: Type of elements (must form a monoid under op)
        ActionT: Type of lazy propagation values (must form a monoid under composition)

    Args:
        op: Binary operation for ValueT (associative)
        e: Identity element for op
        mapping: Function to apply ActionT to ValueT
        composition: Binary operation for ActionT (associative)
        id: Identity element for composition
        commutative: If True, the caller guarantees that op is commutative.

    Examples:
        >>> # Range sum with range add
        >>> def op(a, b): return (a[0] + b[0], a[1] + b[1])
        >>> def mapping(f, x): return (x[0] + f * x[1], x[1])
        >>> def composition(f, g): return f + g
        >>> treap = ImplicitTreap(op, (0, 0), mapping, composition, 0)
        >>> treap.build([(x, 1) for x in [1, 2, 3, 4, 5]])
        >>> treap.range_apply(1, 4, 10)  # Add 10 to elements at positions [1, 4)
        >>> print(treap.prod(0, 5)[0])  # Sum of all elements
        45

    Space Complexity:
        O(m), where m is the maximum size since the last build. Deleted slots are reused.

    Callback Contract:
        op is associative with identity e and need not be commutative.
        mapping(f, op(a, b)) must equal op(mapping(f, a), mapping(f, b)),
        and mapping(f, e) must equal e. Encode segment length in ValueT
        when an update, such as adding to a sum, depends on that length.
        composition(f, g) applies g first, then f. id leaves values unchanged.
        Callbacks must not mutate their inputs. Complexity bounds assume
        O(1) callback cost and fixed-size values.
    """
    __slots__ = ['root', 'op', 'e', 'mapping', 'composition', 'id', 'val', 'pri', 'ptr', 'cnt', 'acc', '_racc', '_commutative', 'laz', 'rand', '_free']

    def __init__(self, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[[ActionT, ValueT], ValueT], composition: Callable[[ActionT, ActionT], ActionT], id: ActionT, *, commutative: bool = False) -> None:
        """Initialize ImplicitTreap with monoid operations with no elements.

        Args:
            op: Binary operation for ValueT (must be associative)
            e: Identity element for op
            mapping: Function to apply lazy value ActionT to element ValueT
            composition: Binary operation for ActionT (must be associative)
            id: Identity element for composition
            commutative: If True, skip reverse aggregates; op must be commutative.

        Time Complexity:
            O(1)

        Returns:
            None.
        """
        self.root = 0
        self._free: list[int] = []
        self.op = op
        self.e = e
        self.mapping = mapping
        self.composition = composition
        self.id = id
        self.val: list[ValueT] = [e]
        self.pri: list[int] = [1 << 32]
        self.ptr: list[int] = [0, 0, 0]
        self.cnt: list[int] = [0]
        self.acc: list[ValueT] = [e]
        self._commutative = commutative
        self._racc: list[ValueT] = [] if commutative else [e]
        self.laz: list[ActionT] = [id]
        self.rand = self._xor64()

    def _xor64(self) -> Iterator[int]:
        x = 88172645463325252
        while True:
            x = x ^ ((x << 7) & 0xffffffff)
            x = x ^ (x >> 9)
            yield x & 0xffffffff

    def _newnode(self, x: ValueT) -> int:
        if self._free:
            idx = self._free.pop()
            self.val[idx] = self.acc[idx] = x
            if not self._commutative:
                self._racc[idx] = x
            self.pri[idx] = next(self.rand)
            self.ptr[idx * 3] = self.ptr[idx * 3 + 1] = self.ptr[idx * 3 + 2] = 0
            self.cnt[idx] = 1
            self.laz[idx] = self.id
            return idx
        idx = len(self.val)
        self.val.append(x)
        self.pri.append(next(self.rand))
        self.ptr.extend([0, 0, 0])
        self.cnt.append(1)
        self.acc.append(x)
        if not self._commutative:
            self._racc.append(x)
        self.laz.append(self.id)
        return idx

    def _push(self, t: int) -> None:
        ptr, laz = self.ptr, self.laz
        if ptr[t * 3 + 2]:
            ptr[t * 3 + 2] = 0
            l, r = ptr[t * 3], ptr[t * 3 + 1] = ptr[t * 3 + 1], ptr[t * 3]
            if l:
                ptr[l * 3 + 2] ^= 1
                if not self._commutative:
                    self.acc[l], self._racc[l] = self._racc[l], self.acc[l]
            if r:
                ptr[r * 3 + 2] ^= 1
                if not self._commutative:
                    self.acc[r], self._racc[r] = self._racc[r], self.acc[r]
        if laz[t] != self.id:
            l, r = ptr[t * 3], ptr[t * 3 + 1]
            acc, val = self.acc, self.val
            if l:
                laz[l] = self.composition(laz[t], laz[l])
                acc[l] = self.mapping(laz[t], acc[l])
                if not self._commutative:
                    self._racc[l] = self.mapping(laz[t], self._racc[l])
            if r:
                laz[r] = self.composition(laz[t], laz[r])
                acc[r] = self.mapping(laz[t], acc[r])
                if not self._commutative:
                    self._racc[r] = self.mapping(laz[t], self._racc[r])
            val[t] = self.mapping(laz[t], val[t])
            laz[t] = self.id

    def _update(self, t: int) -> None:
        ptr, cnt, acc, val, op = self.ptr, self.cnt, self.acc, self.val, self.op
        l, r = ptr[t * 3], ptr[t * 3 + 1]
        cnt[t] = cnt[l] + cnt[r] + 1
        acc[t] = op(op(acc[l], val[t]), acc[r])
        if not self._commutative:
            self._racc[t] = op(op(self._racc[r], val[t]), self._racc[l])

    def _split(self, t: int, k: int, update: bool = False) -> tuple[int, int]:
        ptr, cnt = self.ptr, self.cnt
        l = r = 0
        while t:
            self._push(t)
            p = cnt[ptr[t * 3]] + 1
            if k < p:
                v, ptr[t * 3] = ptr[t * 3], r
                r, t = t, v
            else:
                v, ptr[t * 3 + 1] = ptr[t * 3 + 1], l
                l, t = t, v
                k -= p
        s = 0
        while l:
            v, ptr[l * 3 + 1] = ptr[l * 3 + 1], s
            if update:
                self._update(l)
            s, l = l, v
        l = s
        s = 0
        while r:
            v, ptr[r * 3] = ptr[r * 3], s
            if update:
                self._update(r)
            s, r = r, v
        r = s
        return l, r

    def _merge(self, l: int, r: int, push_lt: bool = False, push_rt: bool = False) -> int:
        ptr, pri = self.ptr, self.pri
        s = 0
        while l:
            if push_lt:
                self._push(l)
            v, ptr[l * 3 + 1] = ptr[l * 3 + 1], s
            s, l = l, v
        l = s
        s = 0
        while r:
            if push_rt:
                self._push(r)
            v, ptr[r * 3] = ptr[r * 3], s
            s, r = r, v
        r = s
        t = 0
        while l or r:
            if pri[l] < pri[r]:
                v, ptr[l * 3 + 1] = ptr[l * 3 + 1], t
                self._update(l)
                t, l = l, v
            else:
                v, ptr[r * 3] = ptr[r * 3], t
                self._update(r)
                t, r = r, v
        return t

    def build(self, arr: list[ValueT]) -> None:
        """
        Build treap from array.

        Args:
            arr: Array to build treap from

        Notes:
            Uses optimized construction that maintains heap property.

        Time Complexity:
            O(n), where n = len(arr).

        Returns:
            None.
        """
        self._free.clear()
        self.root = 0
        n = len(arr)
        val = self.val = [self.e] + arr
        pri = self.pri = [1 << 32] + [next(self.rand) for _ in range(n)]
        ptr = self.ptr = [0] * (n * 3 + 3)
        cnt = self.cnt = [0] + [1] * n
        acc = self.acc = [self.e] * (n + 1)
        self._racc = [] if self._commutative else [self.e] * (n + 1)
        self.laz = [self.id] * (n + 1)
        if n == 0:
            return
        op = self.op
        par = [0] * (n + 1)
        for i in range(2, n + 1):
            p = i - 1
            l = 0
            while p and pri[i] > pri[p]:
                pp = par[p]
                if l:
                    par[l] = p
                par[p] = i
                l, p = p, pp
            par[i] = p
        for i, p in enumerate(par):
            if not p:
                self.root = i
            elif i < p:
                ptr[p * 3] = i
            else:
                ptr[p * 3 + 1] = i
        stack: list[int] = [self.root]
        ord: list[int] = []
        while stack:
            v = stack.pop()
            ord.append(v)
            l, r = ptr[v * 3], ptr[v * 3 + 1]
            if l:
                stack.append(l)
            if r:
                stack.append(r)
        for v in ord[::-1]:
            l, r = ptr[v * 3], ptr[v * 3 + 1]
            cnt[v] = cnt[l] + cnt[r] + 1
            acc[v] = op(op(acc[l], val[v]), acc[r])
            if not self._commutative:
                self._racc[v] = op(op(self._racc[r], val[v]), self._racc[l])

    def size(self) -> int:
        """
        Get number of elements in treap.

        Returns:
            Number of elements

        Time Complexity:
            O(1)
        """
        return self.cnt[self.root]

    def insert(self, pos: int, x: ValueT) -> None:
        """
        Insert element at position.

        Args:
            pos: Position to insert at (0-indexed)
            x: Element to insert

        Time Complexity:
            Expected ``O(log n)``

        Returns:
            None.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= pos <= self.size():
            raise IndexError('insert position out of range')
        l, r = self._split(self.root, pos)
        self.root = self._merge(self._merge(l, self._newnode(x)), r)

    def erase(self, pos: int) -> None:
        """
        Erase element at position.

        Args:
            pos: Position to erase (0-indexed)

        Time Complexity:
            Expected ``O(log n)``

        Returns:
            None.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= pos < self.size():
            raise IndexError('erase position out of range')
        l, r = self._split(self.root, pos + 1)
        l, removed = self._split(l, pos)
        self.root = self._merge(l, r)
        self.val[removed] = self.acc[removed] = self.e
        if not self._commutative:
            self._racc[removed] = self.e
        self.laz[removed] = self.id
        self._free.append(removed)

    def get(self, pos: int) -> ValueT:
        """
        Get element at position.

        Args:
            pos: Position to get (0-indexed)

        Returns:
            Element at position

        Time Complexity:
            Expected ``O(log n)``

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= pos < self.size():
            raise IndexError('get position out of range')
        t1, t2 = self._split(self.root, pos + 1, True)
        t1, t3 = self._split(t1, pos, True)
        res = self.val[t3]
        self.root = self._merge(self._merge(t1, t3), t2)
        return res

    def reverse(self, l: int, r: int) -> None:
        """
        Reverse subsequence [l, r).

        Args:
            l: Left boundary (inclusive)
            r: Right boundary (exclusive)

        Time Complexity:
            Expected ``O(log n)``

        Returns:
            None.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= l <= r <= self.size():
            raise IndexError('range out of bounds')
        if l == r:
            return
        t2, t3 = self._split(self.root, r)
        t1, t2 = self._split(t2, l)
        self.ptr[t2 * 3 + 2] ^= 1
        if not self._commutative:
            self.acc[t2], self._racc[t2] = self._racc[t2], self.acc[t2]
        self.root = self._merge(self._merge(t1, t2, False, True), t3, True, False)

    def range_apply(self, l: int, r: int, x: ActionT) -> None:
        """
        Apply a lazy value to the range ``[l, r)`` in place.

        Args:
            l: Inclusive left boundary; requires ``0 <= l <= r <= size()``.
            r: Exclusive right boundary.
            x: Update passed to the mapping operation.

        Returns:
            None.

        Time Complexity:
            Expected ``O(log n)``

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= l <= r <= self.size():
            raise IndexError('range out of bounds')
        if l == r:
            return
        t2, t3 = self._split(self.root, r)
        t1, t2 = self._split(t2, l)
        self.laz[t2] = self.composition(x, self.laz[t2])
        self.root = self._merge(self._merge(t1, t2, False, True), t3, True, False)

    def prod(self, l: int, r: int) -> ValueT:
        """
        Get product of range [l, r) using monoid operation.

        Args:
            l: Left boundary (inclusive)
            r: Right boundary (exclusive)

        Returns:
            Product of elements in range

        Time Complexity:
            Expected ``O(log n)``

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= l <= r <= self.size():
            raise IndexError('range out of bounds')
        if l == r:
            return self.e
        t2, t3 = self._split(self.root, r, True)
        t1, t2 = self._split(t2, l, True)
        res = self.acc[t2]
        self.root = self._merge(self._merge(t1, t2), t3)
        return res

    def iter(self) -> Iterator[ValueT]:
        """
        Iterate over all elements in order.

        Time Complexity:
            ``O(n)``

        Returns:
            Iterator over elements in sequence order.
        """
        stack: list[int] = []
        v = self.root
        while stack or v:
            while v:
                self._push(v)
                stack.append(v)
                v = self.ptr[v * 3]
            v = stack.pop()
            yield self.val[v]
            v = self.ptr[v * 3 + 1]


class Treap(Generic[KeyT]):
    """
    Treap implementation for ordered set operations.

    A Treap (tree + heap) is a randomized binary search tree that maintains
    both BST property (by key) and heap property (by random priority).
    Provides expected O(log n) operations for dynamic ordered sets.

    Time Complexities:
        - add/discard/remove: O(log n) expected
        - contains/get: O(log n) expected
        - bisect_left/bisect_right: O(log n) expected
        - successor/predecessor: O(log n) expected
        - build: O(n log n) expected

    Type Parameters:
        KeyT: Type that supports comparison operations

    Examples:
        >>> treap = Treap[int]()
        >>> treap.add(5)
        True
        >>> treap.add(3)
        True
        >>> treap.add(7)
        True
        >>> print(treap.size())  # 3
        3
        >>> print(treap.contains(5))
        True
        >>> idx = treap.bisect_left(4)
        >>> val = treap.successor(4)
        >>> print(val)  # 5 (smallest element >= 4)
        5

    Notes:
        Keys are equivalent when neither compares less than the other;
        equality does not require __eq__.
        Node index 0 represents an absent node; its key is never read.
        The key array starts empty. The first node allocation also fills
        slot 0 with the first key, keeping stored keys typed as KeyT.

    Space Complexity:
        O(m), where m is the maximum number of stored keys since the last
        build. Deleted node slots are reused by later insertions.
    """
    __slots__ = ['root', 'key', 'pri', 'lt', 'rt', 'cnt', 'rand', '_free']

    def __init__(self) -> None:
        """Initialize empty treap.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.root = 0
        self._free: list[int] = []
        self.key: list[KeyT] = []
        self.pri: list[int] = [1 << 32]
        self.lt: list[int] = [0]
        self.rt: list[int] = [0]
        self.cnt: list[int] = [0]
        self.rand = self._xor32_()

    def _xor32_(self) -> Iterator[int]:
        x = 2463534242
        while True:
            x = x ^ ((x << 13) & 0xffffffff)
            x = x ^ ((x >> 17))
            x = x ^ ((x << 5) & 0xffffffff)
            yield x

    def _newnode_(self, x: KeyT) -> int:
        if self._free:
            idx = self._free.pop()
            self.key[idx] = x
            self.pri[idx] = next(self.rand)
            self.lt[idx] = self.rt[idx] = 0
            self.cnt[idx] = 1
            return idx
        if not self.key:
            self.key.append(x)  # Unused slot for the absent node at index 0.
        idx = len(self.key)
        self.key.append(x)
        self.pri.append(next(self.rand))
        self.lt.append(0)
        self.rt.append(0)
        self.cnt.append(1)
        return idx

    def _update_(self, t: int) -> None:
        lt, rt, cnt = self.lt, self.rt, self.cnt
        l, r = lt[t], rt[t]
        cnt[t] = cnt[l] + cnt[r] + 1

    def build(self, keys: list[KeyT], is_sorted: bool = False) -> None:
        """
        Replace the set with the distinct values in ``keys``.

        Args:
            keys: Keys to store. Duplicate keys are removed; an empty list clears the set.
            is_sorted: If True, assumes keys are already sorted.

        Returns:
            None.

        Notes:
            Uses optimized construction that maintains heap property.

        Time Complexity:
            O(n log n), or O(n) if is_sorted=True, where n = len(keys).
        """
        self._free.clear()
        if not is_sorted:
            keys = sorted(keys)
        distinct: list[KeyT] = []
        for key in keys:
            if not distinct or distinct[-1] < key:
                distinct.append(key)
        n = len(distinct)
        self.key = [distinct[0]] + distinct if distinct else []
        pri = self.pri = [1 << 32] + [next(self.rand) for _ in range(n)]
        lt = self.lt = [0] * (n + 1)
        rt = self.rt = [0] * (n + 1)
        cnt = self.cnt = [0] + [1] * n
        if n == 0:
            self.root = 0
            return
        par = [0] * (n + 1)
        for i in range(2, n + 1):
            p = i - 1
            l = 0
            while p and pri[i] > pri[p]:
                pp = par[p]
                if l:
                    par[l] = p
                par[p] = i
                l, p = p, pp
            par[i] = p
        for i, p in enumerate(par):
            if not p:
                self.root = i
            elif i < p:
                lt[p] = i
            else:
                rt[p] = i
        stack: list[int] = [self.root]
        ord: list[int] = []
        while stack:
            v = stack.pop()
            ord.append(v)
            l, r = lt[v], rt[v]
            if l:
                stack.append(l)
            if r:
                stack.append(r)
        for v in ord[::-1]:
            l, r = lt[v], rt[v]
            cnt[v] = cnt[l] + cnt[r] + 1

    def _split_(self, t: int, k: KeyT, eq: bool = True) -> tuple[int, int]:
        lt, rt, key = self.lt, self.rt, self.key
        l = r = 0
        if eq:
            while t:
                if k < key[t]:
                    v, lt[t] = lt[t], r
                    r, t = t, v
                else:
                    v, rt[t] = rt[t], l
                    l, t = t, v
        else:
            while t:
                if key[t] < k:
                    v, rt[t] = rt[t], l
                    l, t = t, v
                else:
                    v, lt[t] = lt[t], r
                    r, t = t, v
        s = 0
        while l:
            v, rt[l] = rt[l], s
            self._update_(l)
            s, l = l, v
        l = s
        s = 0
        while r:
            v, lt[r] = lt[r], s
            self._update_(r)
            s, r = r, v
        r = s
        return l, r

    def _split_with_find_(self, t: int, k: KeyT, eq: bool = True) -> tuple[int, int, bool]:
        lt, rt, key = self.lt, self.rt, self.key
        l = r = 0
        found = False
        if eq:
            while t:
                if not key[t] < k and not k < key[t]:
                    found = True
                if k < key[t]:
                    v, lt[t] = lt[t], r
                    r, t = t, v
                else:
                    v, rt[t] = rt[t], l
                    l, t = t, v
        else:
            while t:
                if not key[t] < k and not k < key[t]:
                    found = True
                if key[t] < k:
                    v, rt[t] = rt[t], l
                    l, t = t, v
                else:
                    v, lt[t] = lt[t], r
                    r, t = t, v
        s = 0
        while l:
            v, rt[l] = rt[l], s
            self._update_(l)
            s, l = l, v
        l = s
        s = 0
        while r:
            v, lt[r] = lt[r], s
            self._update_(r)
            s, r = r, v
        r = s
        return l, r, found

    def _merge_(self, l: int, r: int) -> int:
        lt, rt, pri = self.lt, self.rt, self.pri
        s = 0
        while l:
            v, rt[l] = rt[l], s
            s, l = l, v
        l = s
        s = 0
        while r:
            v, lt[r] = lt[r], s
            s, r = r, v
        r = s
        t = 0
        while l or r:
            if pri[l] < pri[r]:
                v, rt[l] = rt[l], t
                self._update_(l)
                t, l = l, v
            else:
                v, lt[r] = lt[r], t
                self._update_(r)
                t, r = r, v
        return t

    def _iter_(self, t: int) -> Iterator[KeyT]:
        stack: list[int] = []
        while t or stack:
            while t:
                stack.append(t)
                t = self.lt[t]
            t = stack.pop()
            yield self.key[t]
            t = self.rt[t]

    def size(self) -> int:
        """
        Get number of elements in treap.

        Returns:
            Number of elements

        Time Complexity:
            O(1)
        """
        return self.cnt[self.root]

    def iter(self) -> Iterator[KeyT]:
        """
        Iterate over all elements in sorted order.

        Returns:
            Iterator over the stored keys in ascending order.

        Time Complexity:
            ``O(n)``
        """
        yield from self._iter_(self.root)

    def iter_range(self, left: KeyT, right: KeyT) -> Iterator[KeyT]:
        """
        Iterate over keys ``x`` such that ``left <= x <= right``.

        Args:
            left: Inclusive lower bound.
            right: Inclusive upper bound.

        Returns:
            Iterator over matching keys in ascending order.

        Time Complexity:
            Expected ``O(log n + k)``, where ``k`` is the number of yielded keys.

        Space Complexity:
            Expected ``O(log n)`` for the traversal stack.
        """
        stack: list[int] = []
        v = self.root
        key = self.key
        lt = self.lt
        rt = self.rt
        while stack or v:
            while v:
                if key[v] < left:
                    v = rt[v]
                else:
                    stack.append(v)
                    v = lt[v]
            if not stack:
                break
            v = stack.pop()
            if right < key[v]:
                break
            yield key[v]
            v = rt[v]

    def add(self, k: KeyT, validity_check: bool = True) -> bool:
        """
        Add key to treap.

        Args:
            k: Key to add
            validity_check: If False, the caller must guarantee that the key is absent.

        Returns:
            True if added, otherwise False. With ``validity_check=False``, success is assumed.

        Notes:
            With ``validity_check=False``, inserting an existing key violates
            the set invariant. Use this path only when absence is guaranteed.

        Time Complexity:
            Expected ``O(log n)``
        """
        if validity_check:
            l, r, found = self._split_with_find_(self.root, k)
            if found:
                self.root = self._merge_(l, r)
                return False
        else:
            l, r = self._split_(self.root, k)
        self.root = self._merge_(self._merge_(l, self._newnode_(k)), r)
        return True

    def discard(self, k: KeyT, validity_check: bool = True) -> bool:
        """
        Remove the specified value if present.

        Args:
            k: Value to remove.
            validity_check: If False, the caller must guarantee that the key exists.

        Returns:
            True if removed, otherwise False. With ``validity_check=False``, success is assumed.

        Notes:
            Passing an absent key with ``validity_check=False`` violates the precondition.
            The return value does not validate that precondition. Both modes
            perform the splits and merge; only the missing-key test is skipped.

        Examples:
            >>> tree = Treap[int]()
            >>> tree.add(5, validity_check=False)
            True
            >>> tree.discard(5, validity_check=False)
            True
            >>> tree.discard(5)
            False

        Time Complexity:
            Expected O(log n), where n is the number of stored keys.
        """
        l, r = self._split_(self.root, k, True)
        l, m = self._split_(l, k, False)
        if validity_check and not m:
            self.root = self._merge_(l, r)
            return False
        self.root = self._merge_(l, r)
        self._free.append(m)
        return True

    def remove(self, k: KeyT) -> None:
        """
        Remove key from treap.

        Args:
            k: Key to delete.

        Returns:
            None.

        Raises:
            KeyError: If ``k`` is not present.

        Time Complexity:
            Expected ``O(log n)``
        """
        if not self.discard(k):
            raise KeyError(k)

    def index(self, k: KeyT) -> int:
        """
        Return the first sorted index of ``k``.

        Args:
            k: Search value.

        Returns:
            Zero-based index of the first occurrence.

        Raises:
            ValueError: If the value is absent.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            Expected O(log n), where n is the number of stored elements.
        """
        node = self.root
        rank = 0
        left, right, keys, counts = self.lt, self.rt, self.key, self.cnt
        while node:
            if k < keys[node]:
                node = left[node]
            elif keys[node] < k:
                rank += counts[left[node]] + 1
                node = right[node]
            else:
                return rank + counts[left[node]]
        raise ValueError('given value is not contained')

    def bisect_left(self, k: KeyT) -> int:
        """
        Return the number of elements strictly less than ``k``.

        Args:
            k: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            Expected O(log n), where n is the number of stored elements.
        """
        node = self.root
        rank = 0
        left, right, keys, counts = self.lt, self.rt, self.key, self.cnt
        while node:
            if keys[node] < k:
                rank += counts[left[node]] + 1
                node = right[node]
            else:
                node = left[node]
        return rank

    def bisect_right(self, k: KeyT) -> int:
        """
        Return the number of elements less than or equal to ``k``.

        Args:
            k: Search value.

        Returns:
            Insertion index in sorted order, from zero through the size.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            Expected O(log n), where n is the number of stored elements.
        """
        node = self.root
        rank = 0
        left, right, keys, counts = self.lt, self.rt, self.key, self.cnt
        while node:
            if k < keys[node]:
                node = left[node]
            else:
                rank += counts[left[node]] + 1
                node = right[node]
        return rank

    def successor(self, k: KeyT, inclusive: bool = True) -> KeyT | None:
        """Return the smallest stored key greater than or equal to ``k``.

        Args:
            k: Search key; it need not be present.
            inclusive: If False, require a key strictly greater than the search key.

        Returns:
            Matching stored key, or None if no such key exists.

        Notes:
            Ordering uses only <. If inclusive is False, all keys equivalent
            to the search key under this ordering are skipped.

        Time Complexity:
            Expected O(log n), where n is the number of stored keys.

        Space Complexity:
            O(1) auxiliary space.
        """
        node = self.root
        result: KeyT | None = None
        left, right, keys = self.lt, self.rt, self.key
        while node:
            matches = not keys[node] < k if inclusive else k < keys[node]
            if matches:
                result = keys[node]
                node = left[node]
            else:
                node = right[node]
        return result

    def predecessor(self, k: KeyT, inclusive: bool = True) -> KeyT | None:
        """Return the largest stored key less than or equal to ``k``.

        Args:
            k: Search key; it need not be present.
            inclusive: If False, require a key strictly less than the search key.

        Returns:
            Matching stored key, or None if no such key exists.

        Notes:
            Ordering uses only <. If inclusive is False, all keys equivalent
            to the search key under this ordering are skipped.

        Time Complexity:
            Expected O(log n), where n is the number of stored keys.

        Space Complexity:
            O(1) auxiliary space.
        """
        node = self.root
        result: KeyT | None = None
        left, right, keys = self.lt, self.rt, self.key
        while node:
            matches = not k < keys[node] if inclusive else keys[node] < k
            if matches:
                result = keys[node]
                node = right[node]
            else:
                node = left[node]
        return result

    def contains(self, k: KeyT) -> bool:
        """
        Check if key exists in treap.

        Args:
            k: Key to search for

        Returns:
            Whether ``k`` exists.

        Time Complexity:
            Expected ``O(log n)``
        """
        lt, rt, key = self.lt, self.rt, self.key
        v = self.root
        while v:
            if k < key[v]:
                v = lt[v]
            elif key[v] < k:
                v = rt[v]
            else:
                return True
        return False

    def get(self, idx: int) -> KeyT:
        """
        Get element by index (0-indexed).

        Args:
            idx: Index in sorted order

        Returns:
            Stored key at the given index.

        Raises:
            IndexError: If idx is outside [0, size()). Negative indices are not supported.

        Time Complexity:
            Expected ``O(log n)``
        """
        if not 0 <= idx < self.size():
            raise IndexError('index out of range')
        v = self.root
        lt, rt, key, cnt = self.lt, self.rt, self.key, self.cnt
        while True:
            s = cnt[lt[v]]
            if s == idx:
                return key[v]
            if s > idx:
                v = lt[v]
            else:
                idx -= s + 1
                v = rt[v]


class TreapMultiset(Generic[KeyT]):
    """
    Treap implementation for ordered multiset operations.

    Each distinct key is stored in one node with its multiplicity. Order
    statistics count duplicate elements.

    Notes:
        Keys are equivalent when neither compares less than the other;
        equality does not require __eq__.
        Node index 0 represents an absent node; its key is never read.
        The key array starts empty. The first node allocation also fills
        slot 0 with the first key, keeping stored keys typed as KeyT.

    Space Complexity:
        O(m), where m is the maximum number of distinct keys since the last
        build. Deleted node slots are reused by later insertions.
    """
    __slots__ = ['root', 'key', 'pri', 'lt', 'rt', 'cnt', 'key_count', 'distinct_cnt', 'rand', '_free']

    def __init__(self) -> None:
        """Initialize empty multiset treap.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.root = 0
        self._free: list[int] = []
        self.key: list[KeyT] = []
        self.pri: list[int] = [1 << 32]
        self.lt: list[int] = [0]
        self.rt: list[int] = [0]
        self.cnt: list[int] = [0]
        self.key_count: list[int] = [0]
        self.distinct_cnt: list[int] = [0]
        self.rand = self._xor32_()

    def _xor32_(self) -> Iterator[int]:
        x = 2463534242
        while True:
            x = x ^ ((x << 13) & 0xffffffff)
            x = x ^ ((x >> 17))
            x = x ^ ((x << 5) & 0xffffffff)
            yield x

    def _newnode_(self, x: KeyT, count: int) -> int:
        if self._free:
            idx = self._free.pop()
            self.key[idx] = x
            self.pri[idx] = next(self.rand)
            self.lt[idx] = self.rt[idx] = 0
            self.cnt[idx] = self.key_count[idx] = count
            self.distinct_cnt[idx] = 1
            return idx
        if not self.key:
            self.key.append(x)  # Unused slot for the absent node at index 0.
        idx = len(self.key)
        self.key.append(x)
        self.pri.append(next(self.rand))
        self.lt.append(0)
        self.rt.append(0)
        self.cnt.append(count)
        self.key_count.append(count)
        self.distinct_cnt.append(1)
        return idx

    def _update_(self, t: int) -> None:
        lt, rt, cnt, distinct_cnt = self.lt, self.rt, self.cnt, self.distinct_cnt
        l, r = lt[t], rt[t]
        cnt[t] = cnt[l] + cnt[r] + self.key_count[t]
        distinct_cnt[t] = distinct_cnt[l] + distinct_cnt[r] + 1

    def _split_(self, t: int, k: KeyT, eq: bool = True) -> tuple[int, int]:
        lt, rt, key = self.lt, self.rt, self.key
        l = r = 0
        if eq:
            while t:
                if k < key[t]:
                    v, lt[t] = lt[t], r
                    r, t = t, v
                else:
                    v, rt[t] = rt[t], l
                    l, t = t, v
        else:
            while t:
                if key[t] < k:
                    v, rt[t] = rt[t], l
                    l, t = t, v
                else:
                    v, lt[t] = lt[t], r
                    r, t = t, v
        s = 0
        while l:
            v, rt[l] = rt[l], s
            self._update_(l)
            s, l = l, v
        l = s
        s = 0
        while r:
            v, lt[r] = lt[r], s
            self._update_(r)
            s, r = r, v
        r = s
        return l, r

    def _merge_(self, l: int, r: int) -> int:
        lt, rt, pri = self.lt, self.rt, self.pri
        s = 0
        while l:
            v, rt[l] = rt[l], s
            s, l = l, v
        l = s
        s = 0
        while r:
            v, lt[r] = lt[r], s
            s, r = r, v
        r = s
        t = 0
        while l or r:
            if pri[l] < pri[r]:
                v, rt[l] = rt[l], t
                self._update_(l)
                t, l = l, v
            else:
                v, lt[r] = lt[r], t
                self._update_(r)
                t, r = r, v
        return t

    def _find_(self, k: KeyT) -> tuple[int, list[int]]:
        key, lt, rt = self.key, self.lt, self.rt
        v = self.root
        path: list[int] = []
        while v:
            path.append(v)
            if k < key[v]:
                v = lt[v]
            elif key[v] < k:
                v = rt[v]
            else:
                return v, path
        return 0, path

    def _iter_(self, t: int) -> Iterator[KeyT]:
        stack: list[int] = []
        while t or stack:
            while t:
                stack.append(t)
                t = self.lt[t]
            t = stack.pop()
            for _ in range(self.key_count[t]):
                yield self.key[t]
            t = self.rt[t]

    def _items_(self, t: int) -> Iterator[tuple[KeyT, int]]:
        stack: list[int] = []
        while t or stack:
            while t:
                stack.append(t)
                t = self.lt[t]
            t = stack.pop()
            yield self.key[t], self.key_count[t]
            t = self.rt[t]

    def build(self, keys: list[KeyT], is_sorted: bool = False) -> None:
        """Replace the multiset with the values in ``keys``.

        Args:
            keys: Keys to store, including duplicates. An empty list clears the multiset.
            is_sorted: If True, assumes keys are already sorted.

        Returns:
            None.

        Time Complexity:
            O(n log n), or O(n) if is_sorted=True, where n = len(keys).
        """
        self._free.clear()
        if not is_sorted:
            keys = sorted(keys)
        distinct: list[KeyT] = []
        counts: list[int] = []
        for k in keys:
            if distinct and not distinct[-1] < k:
                counts[-1] += 1
            else:
                distinct.append(k)
                counts.append(1)
        n = len(distinct)
        self.key = [distinct[0]] + distinct if distinct else []
        pri = self.pri = [1 << 32] + [next(self.rand) for _ in range(n)]
        lt = self.lt = [0] * (n + 1)
        rt = self.rt = [0] * (n + 1)
        cnt = self.cnt = [0] + counts[:]
        self.key_count = [0] + counts
        distinct_cnt = self.distinct_cnt = [0] + [1] * n
        if n == 0:
            self.root = 0
            return
        par = [0] * (n + 1)
        for i in range(2, n + 1):
            p = i - 1
            l = 0
            while p and pri[i] > pri[p]:
                pp = par[p]
                if l:
                    par[l] = p
                par[p] = i
                l, p = p, pp
            par[i] = p
        for i, p in enumerate(par):
            if not p:
                self.root = i
            elif i < p:
                lt[p] = i
            else:
                rt[p] = i
        stack: list[int] = [self.root]
        ord: list[int] = []
        while stack:
            v = stack.pop()
            ord.append(v)
            l, r = lt[v], rt[v]
            if l:
                stack.append(l)
            if r:
                stack.append(r)
        for v in ord[::-1]:
            l, r = lt[v], rt[v]
            cnt[v] = cnt[l] + cnt[r] + self.key_count[v]
            distinct_cnt[v] = distinct_cnt[l] + distinct_cnt[r] + 1

    def size(self) -> int:
        """Get total number of elements, including duplicates.

        Returns:
            Total number of elements.

        Time Complexity:
            O(1)
        """
        return self.cnt[self.root]

    def distinct_size(self) -> int:
        """Get number of distinct elements.

        Returns:
            Number of distinct keys.

        Time Complexity:
            O(1)
        """
        return self.distinct_cnt[self.root]

    def iter(self) -> Iterator[KeyT]:
        """Iterate over all elements in sorted order, including duplicates.

        Returns:
            Iterator over all elements.

        Time Complexity:
            ``O(n)`` where n is the total number of elements.
        """
        yield from self._iter_(self.root)

    def items(self) -> Iterator[tuple[KeyT, int]]:
        """Iterate over distinct keys and their counts in sorted order.

        Returns:
            Iterator over ``(key, count)`` pairs.

        Time Complexity:
            ``O(d)`` where d is the number of distinct keys.
        """
        yield from self._items_(self.root)

    def iter_range(self, left: KeyT, right: KeyT) -> Iterator[KeyT]:
        """
        Iterate over elements ``x`` such that ``left <= x <= right``.

        Duplicate elements are yielded according to their multiplicity.

        Args:
            left: Inclusive lower bound.
            right: Inclusive upper bound.

        Returns:
            Iterator over matching elements in ascending order.

        Time Complexity:
            Expected ``O(log d + k)``, where ``d`` is the number of distinct
            keys and ``k`` is the number of yielded elements.

        Space Complexity:
            Expected ``O(log d)`` for the traversal stack.
        """
        stack: list[int] = []
        v = self.root
        key = self.key
        lt = self.lt
        rt = self.rt
        key_count = self.key_count
        while stack or v:
            while v:
                if key[v] < left:
                    v = rt[v]
                else:
                    stack.append(v)
                    v = lt[v]
            if not stack:
                break
            v = stack.pop()
            if right < key[v]:
                break
            for _ in range(key_count[v]):
                yield key[v]
            v = rt[v]

    def add(self, k: KeyT, count: int = 1) -> int:
        """Add ``count`` copies of the key to the multiset.

        Args:
            k: Key to add.
            count: Number of copies to add. Zero is a no-op.

        Returns:
            Number of copies added, equal to ``count``.

        Raises:
            ValueError: If ``count`` is negative. The contents remain unchanged.

        Time Complexity:
            Expected O(log d), where d is the number of distinct keys; O(1) if count is zero.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return 0
        v, path = self._find_(k)
        if v:
            self.key_count[v] += count
            for p in path[::-1]:
                self._update_(p)
            return count
        l, r = self._split_(self.root, k)
        self.root = self._merge_(self._merge_(l, self._newnode_(k, count)), r)
        return count

    def discard(self, k: KeyT, count: int = 1) -> int:
        """
        Remove up to ``count`` copies.

        Args:
            k: Value to remove.
            count: Maximum number of copies to remove. Zero is a no-op.

        Returns:
            Number of copies actually removed; zero if the value is absent.

        Raises:
            ValueError: If ``count`` is negative.

        Time Complexity:
            Expected O(log d), where d is the number of distinct keys.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return 0
        v, path = self._find_(k)
        if not v:
            return 0
        if self.key_count[v] > count:
            self.key_count[v] -= count
            for p in path[::-1]:
                self._update_(p)
            return count
        removed = self.key_count[v]
        l, r = self._split_(self.root, k, True)
        l, m = self._split_(l, k, False)
        self.root = self._merge_(l, r)
        self._free.append(m)
        return removed

    def remove(self, k: KeyT, count: int = 1, validity_check: bool = True) -> None:
        """
        Remove exactly ``count`` copies.

        Args:
            k: Value to remove.
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
            Expected O(log d), where d is the number of distinct keys.
        """
        if count < 0:
            raise ValueError('count must be nonnegative')
        if count == 0:
            return
        if validity_check and self.count(k) < count:
            raise KeyError(k)
        self.discard(k, count)

    def count(self, k: KeyT) -> int:
        """Get multiplicity of key.

        Args:
            k: Key to count.

        Returns:
            Number of copies of key in the multiset.

        Time Complexity:
            Expected ``O(log d)``.
        """
        v, _ = self._find_(k)
        return self.key_count[v] if v else 0

    def contains(self, k: KeyT) -> bool:
        """Check if key exists in the multiset.

        Args:
            k: Key to search for.

        Returns:
            Whether ``k`` exists.

        Time Complexity:
            Expected ``O(log d)``.
        """
        v, _ = self._find_(k)
        return v != 0

    def index(self, k: KeyT) -> int:
        """
        Return the first sorted index of ``k``.

        Args:
            k: Search value.

        Returns:
            Zero-based index of the first occurrence.

        Raises:
            ValueError: If the value is absent.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            Expected O(log d), where d is the number of distinct stored values.
        """
        node = self.root
        rank = 0
        left, right, keys, counts = self.lt, self.rt, self.key, self.cnt
        while node:
            if k < keys[node]:
                node = left[node]
            elif keys[node] < k:
                rank += counts[left[node]] + self.key_count[node]
                node = right[node]
            else:
                return rank + counts[left[node]]
        raise ValueError('given value is not contained')

    def bisect_left(self, k: KeyT) -> int:
        """
        Return the number of elements strictly less than ``k``.

        Args:
            k: Search value.

        Returns:
            Insertion index in sorted order, counting each copy separately.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Examples:
            >>> values = TreapMultiset[int]()
            >>> values.build([2, 5, 5, 9])
            >>> values.bisect_left(5), values.bisect_right(5), values.index(5)
            (1, 3, 1)
            >>> values.bisect_left(4)
            1
            >>> values.index(4)
            Traceback (most recent call last):
                ...
            ValueError: given value is not contained

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            Expected O(log d), where d is the number of distinct stored values.
        """
        node = self.root
        rank = 0
        left, right, keys, counts = self.lt, self.rt, self.key, self.cnt
        while node:
            if keys[node] < k:
                rank += counts[left[node]] + self.key_count[node]
                node = right[node]
            else:
                node = left[node]
        return rank

    def bisect_right(self, k: KeyT) -> int:
        """
        Return the number of elements less than or equal to ``k``.

        Args:
            k: Search value.

        Returns:
            Insertion index in sorted order, counting each copy separately.

        Notes:
            Search values need not be present or lie in the storage range.
            Returns zero below all stored values and the size above them.

        Space Complexity:
            O(1) auxiliary space.

        Time Complexity:
            Expected O(log d), where d is the number of distinct stored values.
        """
        node = self.root
        rank = 0
        left, right, keys, counts = self.lt, self.rt, self.key, self.cnt
        while node:
            if k < keys[node]:
                node = left[node]
            else:
                rank += counts[left[node]] + self.key_count[node]
                node = right[node]
        return rank

    def successor(self, k: KeyT, inclusive: bool = True) -> KeyT | None:
        """Return the smallest stored key greater than or equal to ``k``.

        Args:
            k: Search key; it need not be present.
            inclusive: If False, require a key strictly greater than the search key.

        Returns:
            Matching stored key, or None if no such key exists.

        Notes:
            Ordering uses only <. If inclusive is False, all keys equivalent
            to the search key under this ordering are skipped.

        Time Complexity:
            Expected O(log d), where d is the number of distinct stored keys.

        Space Complexity:
            O(1) auxiliary space.
        """
        node = self.root
        result: KeyT | None = None
        left, right, keys = self.lt, self.rt, self.key
        while node:
            matches = not keys[node] < k if inclusive else k < keys[node]
            if matches:
                result = keys[node]
                node = left[node]
            else:
                node = right[node]
        return result

    def predecessor(self, k: KeyT, inclusive: bool = True) -> KeyT | None:
        """Return the largest stored key less than or equal to ``k``.

        Args:
            k: Search key; it need not be present.
            inclusive: If False, require a key strictly less than the search key.

        Returns:
            Matching stored key, or None if no such key exists.

        Notes:
            Ordering uses only <. If inclusive is False, all keys equivalent
            to the search key under this ordering are skipped.

        Time Complexity:
            Expected O(log d), where d is the number of distinct stored keys.

        Space Complexity:
            O(1) auxiliary space.
        """
        node = self.root
        result: KeyT | None = None
        left, right, keys = self.lt, self.rt, self.key
        while node:
            matches = not k < keys[node] if inclusive else keys[node] < k
            if matches:
                result = keys[node]
                node = right[node]
            else:
                node = left[node]
        return result

    def get(self, idx: int) -> KeyT:
        """Get element by index in sorted order, counting duplicates.

        Args:
            idx: Index in sorted order.

        Returns:
            Stored key at the given index.

        Raises:
            IndexError: If idx is outside [0, size()). Negative indices are not supported.

        Time Complexity:
            Expected ``O(log d)``.
        """
        if not 0 <= idx < self.size():
            raise IndexError('index out of range')
        v = self.root
        lt, rt, key, cnt, key_count = self.lt, self.rt, self.key, self.cnt, self.key_count
        while True:
            s = cnt[lt[v]]
            if idx < s:
                v = lt[v]
            elif idx < s + key_count[v]:
                return key[v]
            else:
                idx -= s + key_count[v]
                v = rt[v]


class SegmentedImplicitTreap(Generic[ValueT, ActionT]):
    """
    Implicit treap whose nodes represent constant segments.

    The sequence is stored as a treap of constant runs instead of single
    elements. This keeps long uniform stretches compact while still allowing
    split, merge, range update, and range aggregation operations.

    Args:
        op: Associative operation used to aggregate segment values.
        e: Identity element for ``op``.
        make_data: Converts a ``(length, value)`` pair into the aggregated
            representation for that segment.
        mapping: Applies a lazy value to a segment aggregate and its base value.
        composition: Composes two lazy values.
        identity: Identity lazy value.

    Time Complexity:
        - ``merge``: expected O(log k), where k is the number of stored segments.
        - ``split`` / ``range_apply`` / ``prod``: expected O(log^2(k + 1))
          upper bound for splitting through repeated merges.

    Space Complexity:
        - O(A), where A is the total number of allocated segment nodes.
          Nodes from roots abandoned by the caller are not reclaimed.

    Examples:
        >>> # A run-length encoded treap for range sums.
        >>> # See the callback definitions used by the concrete data type.
    """

    __slots__ = (
        'lc',
        'rc',
        'prio',
        'segment_len',
        'segment_value',
        'subtree_prod',
        'subtree_len',
        'lazy',
        'op',
        'e',
        'make_data',
        'mapping',
        'composition',
        'identity',
        '_rand',
    )

    def __init__(self, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, make_data: Callable[[int, ValueT], ValueT], mapping: Callable[[ActionT, ValueT, int, ValueT], tuple[ValueT, ValueT]], composition: Callable[[ActionT, ActionT], ActionT], identity: ActionT) -> None:
        """
        Initialize an empty segmented implicit treap.

        Args:
            op: Associative operation used to aggregate segment values.
            e: Identity element for ``op``.
            make_data: Converts a ``(length, value)`` pair into the aggregated representation for that segment.
            mapping: Applies a lazy value to a segment aggregate and its base value.
            composition: Composes two lazy values.
            identity: Identity lazy value.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.lc = [0]
        self.rc = [0]
        self.prio = [0]
        self.segment_len = [0]
        self.segment_value = [e]
        self.subtree_prod = [e]
        self.subtree_len = [0]
        self.lazy = [identity]
        self.op = op
        self.e = e
        self.make_data = make_data
        self.mapping = mapping
        self.composition = composition
        self.identity = identity
        self._rand = self._xor32()

    def _xor32(self) -> Iterator[int]:
        x = 2463534242
        while True:
            x ^= (x << 13) & 0xFFFFFFFF
            x ^= x >> 17
            x ^= (x << 5) & 0xFFFFFFFF
            yield x

    def new_root(self, length: int, value: ValueT) -> int:
        """
        Create a root representing ``length`` copies of ``value``.

        Args:
            length: Length of the sequence.
            value: Segment value.

        Returns:
            Root of the new sequence, or 0 if length is zero.

        Raises:
            ValueError: If ``length`` is negative.

        Time Complexity:
            O(1)
        """
        if length < 0:
            raise ValueError('length must be non-negative')
        if length == 0:
            return 0
        return self._new_node(length, value)

    def _new_node(self, length: int, value: ValueT) -> int:
        idx = len(self.lc)
        self.lc.append(0)
        self.rc.append(0)
        self.prio.append(next(self._rand))
        self.segment_len.append(length)
        self.segment_value.append(value)
        self.subtree_prod.append(value)
        self.subtree_len.append(length)
        self.lazy.append(self.identity)
        self.subtree_prod[idx] = self.make_data(length, value)
        return idx

    def _update(self, node: int) -> None:
        if node == 0:
            return
        left = self.lc[node]
        right = self.rc[node]
        self.subtree_len[node] = self.subtree_len[left] + self.segment_len[node] + self.subtree_len[right]
        self.subtree_prod[node] = self.op(
            self.op(self.subtree_prod[left], self.make_data(self.segment_len[node], self.segment_value[node])),
            self.subtree_prod[right],
        )

    def _apply(self, node: int, lazy_value: ActionT) -> None:
        if node == 0:
            return
        new_prod, new_value = self.mapping(
            lazy_value,
            self.subtree_prod[node],
            self.subtree_len[node],
            self.segment_value[node],
        )
        self.subtree_prod[node] = new_prod
        self.segment_value[node] = new_value
        self.lazy[node] = self.composition(lazy_value, self.lazy[node])

    def _push(self, node: int) -> None:
        if node == 0 or self.lazy[node] == self.identity:
            return
        lazy_value = self.lazy[node]
        self._apply(self.lc[node], lazy_value)
        self._apply(self.rc[node], lazy_value)
        self.lazy[node] = self.identity

    def merge(self, left_root: int, right_root: int) -> int:
        """
        Concatenate two segmented treap roots.

        Args:
            left_root: Root of the left sequence; it must not share nodes with right_root.
            right_root: Root of the right sequence.

        Returns:
            Root of the concatenated sequence. Both input roots are consumed;
            continue only with the returned root.

        Raises:
            ValueError: If the same nonempty root is passed twice.

        Time Complexity:
            Expected ``O(log k)`` where ``k`` is the number of stored segments
        """
        if left_root == 0:
            return right_root
        if right_root == 0:
            return left_root
        if left_root == right_root:
            raise ValueError('cannot merge a sequence with itself')
        stack: list[tuple[int, bool]] = []
        left = left_root
        right = right_root
        while left and right:
            if self.prio[left] > self.prio[right]:
                self._push(left)
                stack.append((left, True))
                left = self.rc[left]
            else:
                self._push(right)
                stack.append((right, False))
                right = self.lc[right]
        tail = left if left else right
        while stack:
            node, attach_right = stack.pop()
            if attach_right:
                self.rc[node] = tail
            else:
                self.lc[node] = tail
            self._update(node)
            tail = node
        return tail

    def split(self, root: int, length: int) -> tuple[int, int]:
        """
        Split a sequence after ``length`` elements.

        Args:
            root: Root of the sequence to split.
            length: Number of elements to put in the left result.

        Returns:
            Pair ``(left_root, right_root)``. The input is consumed; continue
            with the returned roots. Adjacent equal-valued runs are not coalesced.

        Raises:
            ValueError: If ``length`` is outside ``[0, subtree_len[root]]``.

        Time Complexity:
            Expected O(log^2(k + 1)) upper bound, where k is the number of segments.
        """
        if length < 0 or length > self.subtree_len[root]:
            raise ValueError('split length is out of range')
        if length == 0:
            return 0, root
        if length == self.subtree_len[root]:
            return root, 0
        left_root = 0
        right_root = 0
        node = root
        remaining = length
        while node:
            self._push(node)
            left = self.lc[node]
            right = self.rc[node]
            left_size = self.subtree_len[left]
            if remaining < left_size:
                next_node = left
                self.lc[node] = 0
                self._update(node)
                right_root = self.merge(node, right_root)
                node = next_node
            elif remaining > left_size + self.segment_len[node]:
                next_node = right
                taken = left_size + self.segment_len[node]
                self.rc[node] = 0
                self._update(node)
                left_root = self.merge(left_root, node)
                node = next_node
                remaining -= taken
            else:
                take_left = remaining - left_size
                if take_left <= 0:
                    self.lc[node] = 0
                    self._update(node)
                    if left:
                        left_root = self.merge(left_root, left)
                    right_root = self.merge(node, right_root)
                elif take_left >= self.segment_len[node]:
                    self.rc[node] = 0
                    self._update(node)
                    left_root = self.merge(left_root, node)
                    if right:
                        right_root = self.merge(right, right_root)
                else:
                    right_node = self._new_node(self.segment_len[node] - take_left, self.segment_value[node])
                    self.segment_len[node] = take_left
                    self.rc[node] = 0
                    self._update(node)
                    left_root = self.merge(left_root, node)
                    right_root = self.merge(self.merge(right_node, right), right_root)
                break
        return left_root, right_root

    def range_apply(self, root: int, l: int, r: int, lazy_value: ActionT) -> int:
        """
        Apply a lazy value to ``[l, r)``.

        Args:
            root: Root of the sequence.
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.
            lazy_value: Lazy value to apply.

        Returns:
            Root of the updated sequence.

        Raises:
            ValueError: If the range is out of bounds.

        Time Complexity:
            Expected O(log^2(k + 1)) upper bound, where k is the number of segments.
        """
        if not 0 <= l <= r <= self.subtree_len[root]:
            raise ValueError('range is out of bounds')
        if l == r:
            return root
        left, rest = self.split(root, l)
        middle, right = self.split(rest, r - l)
        self._apply(middle, lazy_value)
        return self.merge(left, self.merge(middle, right))

    def prod(self, root: int, l: int, r: int) -> tuple[ValueT, int]:
        """
        Return the aggregate on ``[l, r)``.

        Args:
            root: Root of the sequence.
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.

        Returns:
            Pair ``(aggregate, root)``. The returned root preserves the sequence
            after the internal split/merge operations. Use this returned root
            in subsequent operations; the input root is not a saved version.
            The aggregate is ``e`` if the range is empty.

        Raises:
            ValueError: If the range is out of bounds.

        Time Complexity:
            Expected O(log^2(k + 1)) upper bound, where k is the number of segments.
        """
        if not 0 <= l <= r <= self.subtree_len[root]:
            raise ValueError('range is out of bounds')
        if l == r:
            return self.e, root
        left, rest = self.split(root, l)
        middle, right = self.split(rest, r - l)
        result = self.subtree_prod[middle]
        root = self.merge(left, self.merge(middle, right))
        return result, root
