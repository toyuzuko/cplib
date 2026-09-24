#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import Generic
from cplib.tools.type import ValueT, ActionT


class ImplicitWeightBalancedTree(Generic[ValueT, ActionT]):
    """
    Implicit weight-balanced tree with lazy propagation for sequence operations.

    Positions are represented by subtree sizes. Balance is maintained by subtree
    weights rather than random priorities or heights, so operations have
    logarithmic height without relying on randomization.

    Args:
        op: Associative operation for aggregates.
        e: Identity element for ``op``.
        mapping: Applies a lazy value to one element or aggregate value.
        composition: Composes two lazy values.
        id: Identity lazy value.
        commutative: If True, the caller guarantees that op is commutative.

    Space Complexity:
        O(m), where m is the maximum size since the last build. Deleted slots are reused.

    Complexity Notation:
        ``n`` is the number of stored elements.

    Callback Contract:
        op is associative with identity e and need not be commutative.
        mapping(f, op(a, b)) must equal op(mapping(f, a), mapping(f, b)),
        and mapping(f, e) must equal e. Encode segment length in ValueT
        when an update, such as adding to a sum, depends on that length.
        composition(f, g) applies g first, then f. id leaves values unchanged.
        Callbacks must not mutate their inputs. Complexity bounds assume
        O(1) callback cost and fixed-size values.
    """

    __slots__ = ('root', 'op', 'e', 'mapping', 'composition', 'id', 'val', 'acc', '_racc', '_commutative', 'lazy', 'left', 'right', 'cnt', 'rev', 'free_nodes')

    _DELTA = 4
    _GAMMA = 2

    def __init__(self, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[[ActionT, ValueT], ValueT], composition: Callable[[ActionT, ActionT], ActionT], id: ActionT, *, commutative: bool = False) -> None:
        """Initialize an empty implicit weight-balanced tree.

        Args:
            op: Associative operation for aggregates.
            e: Identity element for ``op``.
            mapping: Function that applies a lazy value to an element or aggregate.
            composition: Function that composes two lazy values.
            id: Identity lazy value.
            commutative: If True, skip reverse aggregates; op must be commutative.

        Time Complexity:
            O(1)

        Returns:
            None.
        """
        self.root = 0
        self.op = op
        self.e = e
        self.mapping = mapping
        self.composition = composition
        self.id = id
        self.val: list[ValueT] = [e]
        self.acc: list[ValueT] = [e]
        self._commutative = commutative
        self._racc: list[ValueT] = [] if commutative else [e]
        self.lazy: list[ActionT] = [id]
        self.left = [0]
        self.right = [0]
        self.cnt = [0]
        self.rev = [False]
        self.free_nodes: list[int] = []

    def _new_node(self, value: ValueT) -> int:
        if self.free_nodes:
            idx = self.free_nodes.pop()
            self.val[idx] = value
            self.acc[idx] = value
            if not self._commutative:
                self._racc[idx] = value
            self.lazy[idx] = self.id
            self.left[idx] = 0
            self.right[idx] = 0
            self.cnt[idx] = 1
            self.rev[idx] = False
            return idx
        idx = len(self.val)
        self.val.append(value)
        self.acc.append(value)
        if not self._commutative:
            self._racc.append(value)
        self.lazy.append(self.id)
        self.left.append(0)
        self.right.append(0)
        self.cnt.append(1)
        self.rev.append(False)
        return idx

    def _free_node(self, node: int) -> None:
        self.val[node] = self.e
        self.acc[node] = self.e
        if not self._commutative:
            self._racc[node] = self.e
        self.lazy[node] = self.id
        self.left[node] = 0
        self.right[node] = 0
        self.cnt[node] = 0
        self.rev[node] = False
        self.free_nodes.append(node)

    def _apply(self, node: int, lazy_value: ActionT) -> None:
        if node == 0:
            return
        self.val[node] = self.mapping(lazy_value, self.val[node])
        self.acc[node] = self.mapping(lazy_value, self.acc[node])
        if not self._commutative:
            self._racc[node] = self.mapping(lazy_value, self._racc[node])
        self.lazy[node] = self.composition(lazy_value, self.lazy[node])

    def _toggle_reverse(self, node: int) -> None:
        if node == 0:
            return
        self.left[node], self.right[node] = self.right[node], self.left[node]
        self.rev[node] ^= True
        if not self._commutative:
            self.acc[node], self._racc[node] = self._racc[node], self.acc[node]

    def _push(self, node: int) -> None:
        left = self.left
        right = self.right
        rev = self.rev
        lazy = self.lazy
        if rev[node]:
            l = left[node]
            if l:
                left[l], right[l] = right[l], left[l]
                rev[l] ^= True
                if not self._commutative:
                    self.acc[l], self._racc[l] = self._racc[l], self.acc[l]
            r = right[node]
            if r:
                left[r], right[r] = right[r], left[r]
                rev[r] ^= True
                if not self._commutative:
                    self.acc[r], self._racc[r] = self._racc[r], self.acc[r]
            rev[node] = False
        lazy_value = lazy[node]
        if lazy_value != self.id:
            mapping = self.mapping
            composition = self.composition
            val = self.val
            acc = self.acc
            l = left[node]
            if l:
                val[l] = mapping(lazy_value, val[l])
                acc[l] = mapping(lazy_value, acc[l])
                if not self._commutative:
                    self._racc[l] = mapping(lazy_value, self._racc[l])
                lazy[l] = composition(lazy_value, lazy[l])
            r = right[node]
            if r:
                val[r] = mapping(lazy_value, val[r])
                acc[r] = mapping(lazy_value, acc[r])
                if not self._commutative:
                    self._racc[r] = mapping(lazy_value, self._racc[r])
                lazy[r] = composition(lazy_value, lazy[r])
            lazy[node] = self.id

    def _update(self, node: int) -> int:
        left = self.left
        right = self.right
        cnt = self.cnt
        acc = self.acc
        l = left[node]
        r = right[node]
        cnt[node] = cnt[l] + cnt[r] + 1
        acc[node] = self.op(self.op(acc[l], self.val[node]), acc[r])
        if not self._commutative:
            self._racc[node] = self.op(self.op(self._racc[r], self.val[node]), self._racc[l])
        return node

    def _rotate_left(self, node: int) -> int:
        right = self.right[node]
        self._push(node)
        self._push(right)
        self.right[node] = self.left[right]
        self.left[right] = self._update(node)
        return self._update(right)

    def _rotate_right(self, node: int) -> int:
        left = self.left[node]
        self._push(node)
        self._push(left)
        self.left[node] = self.right[left]
        self.right[left] = self._update(node)
        return self._update(left)

    def _balance(self, node: int) -> int:
        self._update(node)
        left = self.left
        right = self.right
        cnt = self.cnt
        l = left[node]
        r = right[node]
        if cnt[l] > cnt[r] * self._DELTA + 1:
            self._push(l)
            if cnt[right[l]] > cnt[left[l]] * self._GAMMA:
                left[node] = self._rotate_left(l)
            return self._rotate_right(node)
        if cnt[r] > cnt[l] * self._DELTA + 1:
            self._push(r)
            if cnt[left[r]] > cnt[right[r]] * self._GAMMA:
                right[node] = self._rotate_right(r)
            return self._rotate_left(node)
        return node

    def _build(self, values: list[ValueT]) -> int:
        if not values:
            return 0
        root = 0
        created: list[int] = []
        stack = [(0, len(values), 0, 0)]
        while stack:
            l, r, parent, direction = stack.pop()
            if l >= r:
                continue
            m = (l + r) >> 1
            node = self._new_node(values[m])
            created.append(node)
            if parent == 0:
                root = node
            elif direction == 0:
                self.left[parent] = node
            else:
                self.right[parent] = node
            stack.append((m + 1, r, node, 1))
            stack.append((l, m, node, 0))
        for node in reversed(created):
            self._update(node)
        return root

    def build(self, values: Iterable[ValueT]) -> None:
        """
        Build the tree from values.

        Args:
            values: Initial sequence.

        Time Complexity:
            ``O(n)``

        Returns:
            None.
        """
        arr = list(values)
        self.val = [self.e]
        self.acc = [self.e]
        self._racc = [] if self._commutative else [self.e]
        self.lazy = [self.id]
        self.left = [0]
        self.right = [0]
        self.cnt = [0]
        self.rev = [False]
        self.free_nodes = []
        self.root = self._build(arr)

    def size(self) -> int:
        """
        Return the number of stored elements.

        Returns:
            Number of elements in the current sequence.

        Time Complexity:
            O(1)
        """
        return self.cnt[self.root]

    def __len__(self) -> int:
        """
        Return the number of stored elements.

        Returns:
            Number of elements in the sequence.

        Time Complexity:
            O(1)
        """
        return self.size()

    def _split(self, node: int, k: int) -> tuple[int, int]:
        frames: list[tuple[int, bool]] = []
        while node:
            self._push(node)
            left_size = self.cnt[self.left[node]]
            if k <= left_size:
                frames.append((node, True))
                node = self.left[node]
            else:
                frames.append((node, False))
                k -= left_size + 1
                node = self.right[node]
        left_root = 0
        right_root = 0
        for node, goes_right in reversed(frames):
            if goes_right:
                self.left[node] = right_root
                right_root = self._balance(node)
            else:
                self.right[node] = left_root
                left_root = self._balance(node)
        return left_root, right_root

    def _pop_min(self, node: int) -> tuple[int, int]:
        path: list[int] = []
        self._push(node)
        while self.left[node]:
            path.append(node)
            node = self.left[node]
            self._push(node)
        right = self.right[node]
        self.right[node] = 0
        if not path:
            self._update(node)
            return node, right
        self.left[path[-1]] = right
        new_root = path[0]
        for i in range(len(path) - 1, -1, -1):
            cur = path[i]
            balanced = self._balance(cur)
            if i == 0:
                new_root = balanced
            else:
                parent = path[i - 1]
                if self.left[parent] == cur:
                    self.left[parent] = balanced
                else:
                    self.right[parent] = balanced
        self._update(node)
        return node, new_root

    def _join(self, left_root: int, middle: int, right_root: int) -> int:
        if self.cnt[left_root] > (self.cnt[right_root] + 1) * self._DELTA + 1:
            path: list[int] = []
            node = left_root
            while self.cnt[node] > (self.cnt[right_root] + 1) * self._DELTA + 1:
                self._push(node)
                path.append(node)
                node = self.right[node]
            if node:
                self._push(node)
            self.left[middle] = node
            self.right[middle] = right_root
            self.rev[middle] = False
            self.lazy[middle] = self.id
            subtree = self._update(middle)
            for cur in reversed(path):
                self.right[cur] = subtree
                subtree = self._balance(cur)
            return subtree
        if self.cnt[right_root] > (self.cnt[left_root] + 1) * self._DELTA + 1:
            path = []
            node = right_root
            while self.cnt[node] > (self.cnt[left_root] + 1) * self._DELTA + 1:
                self._push(node)
                path.append(node)
                node = self.left[node]
            if node:
                self._push(node)
            self.left[middle] = left_root
            self.right[middle] = node
            self.rev[middle] = False
            self.lazy[middle] = self.id
            subtree = self._update(middle)
            for cur in reversed(path):
                self.left[cur] = subtree
                subtree = self._balance(cur)
            return subtree
        self.left[middle] = left_root
        self.right[middle] = right_root
        self.rev[middle] = False
        self.lazy[middle] = self.id
        return self._update(middle)

    def _merge(self, left_root: int, right_root: int) -> int:
        if left_root == 0:
            return right_root
        if right_root == 0:
            return left_root
        min_node, right_root = self._pop_min(right_root)
        return self._join(left_root, min_node, right_root)

    def insert(self, pos: int, value: ValueT) -> None:
        """
        Insert ``value`` at position ``pos``.

        Time Complexity:
            ``O(log n)``

        Args:
            pos: Zero-based position in the sequence.
            value: Element to insert.

        Returns:
            None.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        size = self.cnt[self.root]
        if not 0 <= pos <= size:
            raise IndexError('insert position out of range')
        if size == 0:
            self.root = self._new_node(value)
            return
        left_root, right_root = self._split(self.root, pos)
        self.root = self._merge(self._merge(left_root, self._new_node(value)), right_root)

    def erase(self, pos: int) -> None:
        """
        Erase the element at position ``pos``.

        Time Complexity:
            ``O(log n)``

        Args:
            pos: Zero-based position in the sequence.

        Returns:
            None.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        size = self.cnt[self.root]
        if not 0 <= pos < size:
            raise IndexError('erase position out of range')
        left_root, rest = self._split(self.root, pos)
        removed, right_root = self._split(rest, 1)
        if removed:
            self._free_node(removed)
        self.root = self._merge(left_root, right_root)

    def get(self, pos: int) -> ValueT:
        """
        Return the element at position ``pos``.


        Time Complexity:
            ``O(log n)``

        Args:
            pos: Zero-based position in the sequence.

        Returns:
            Stored element at the specified position.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= pos < self.cnt[self.root]:
            raise IndexError('get position out of range')
        node = self.root
        while node:
            self._push(node)
            left_size = self.cnt[self.left[node]]
            if pos == left_size:
                return self.val[node]
            if pos < left_size:
                node = self.left[node]
            else:
                pos -= left_size + 1
                node = self.right[node]
        raise IndexError('get position out of range')

    def reverse(self, l: int, r: int) -> None:
        """
        Reverse the range ``[l, r)``.

        Time Complexity:
            ``O(log n)``

        Args:
            l: Inclusive left boundary.
            r: Exclusive right boundary.

        Returns:
            None.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        size = self.cnt[self.root]
        if not 0 <= l <= r <= size:
            raise IndexError('reverse range out of bounds')
        if l == r:
            return
        if l == 0 and r == size:
            self._toggle_reverse(self.root)
            return
        left_root, rest = self._split(self.root, l)
        middle, right_root = self._split(rest, r - l)
        self._toggle_reverse(middle)
        self.root = self._merge(left_root, self._merge(middle, right_root))

    def range_apply(self, l: int, r: int, lazy_value: ActionT) -> None:
        """
        Apply a lazy value to the range ``[l, r)`` in place.

        Args:
            l: Inclusive left boundary.
            r: Exclusive right boundary.
            lazy_value: Update passed to the mapping operation.

        Returns:
            None.

        Raises:
            IndexError: If ``0 <= l <= r <= size()`` does not hold.

        Time Complexity:
            ``O(log n)``
        """
        size = self.cnt[self.root]
        if not 0 <= l <= r <= size:
            raise IndexError('apply range out of bounds')
        if l == r:
            return
        if l == 0 and r == size:
            self._apply(self.root, lazy_value)
            return
        left_root, rest = self._split(self.root, l)
        middle, right_root = self._split(rest, r - l)
        self._apply(middle, lazy_value)
        self.root = self._merge(left_root, self._merge(middle, right_root))

    def prod(self, l: int, r: int) -> ValueT:
        """
        Return the aggregate of the range ``[l, r)``.

        Args:
            l: Inclusive left boundary.
            r: Exclusive right boundary.

        Returns:
            Aggregate in sequence order, or ``e`` if the range is empty.

        Raises:
            IndexError: If ``0 <= l <= r <= size()`` does not hold.

        Time Complexity:
            ``O(log n)``
        """
        size = self.cnt[self.root]
        if not 0 <= l <= r <= size:
            raise IndexError('prod range out of bounds')
        if l == r:
            return self.e
        if l == 0 and r == size:
            return self.acc[self.root]
        left_root, rest = self._split(self.root, l)
        middle, right_root = self._split(rest, r - l)
        result = self.acc[middle]
        self.root = self._merge(left_root, self._merge(middle, right_root))
        return result

    def iter(self) -> Iterator[ValueT]:
        """
        Iterate over all elements in order.

        Time Complexity:
            ``O(n)``

        Returns:
            Iterator over elements in sequence order.
        """
        stack: list[int] = []
        node = self.root
        while stack or node:
            while node:
                self._push(node)
                stack.append(node)
                node = self.left[node]
            node = stack.pop()
            yield self.val[node]
            node = self.right[node]

    def __iter__(self) -> Iterator[ValueT]:
        """
        Iterate over elements in order.

        Returns:
            Iterator over stored elements.

        Time Complexity:
            O(n)
        """
        return self.iter()


class PersistentImplicitWeightBalancedTree(Generic[ValueT, ActionT]):
    """
    Fully persistent implicit weight-balanced tree with lazy propagation.

    Each update returns a new root while keeping older roots usable. Roots are
    represented by integer handles, and users pass the target root explicitly to
    operations.

    Args:
        op: Associative operation for aggregates.
        e: Identity element for ``op``.
        mapping: Applies a lazy value to one element or aggregate value.
        composition: Composes two lazy values.
        id: Identity lazy value.
        commutative: If True, the caller guarantees that op is commutative.

    Space Complexity:
        O(N)

    Complexity Notation:
        ``N`` is the total number of allocated nodes over all versions.

    Callback Contract:
        op is associative with identity e and need not be commutative.
        mapping(f, op(a, b)) must equal op(mapping(f, a), mapping(f, b)),
        and mapping(f, e) must equal e. Encode segment length in ValueT
        when an update, such as adding to a sum, depends on that length.
        composition(f, g) applies g first, then f. id leaves values unchanged.
        Callbacks must not mutate their inputs. Complexity bounds assume
        O(1) callback cost and fixed-size values.
    """

    __slots__ = ('op', 'e', 'mapping', 'composition', 'id', 'val', 'acc', '_racc', '_commutative', 'lazy', 'left', 'right', 'cnt', 'rev')

    _DELTA = 4
    _GAMMA = 2

    def __init__(self, op: Callable[[ValueT, ValueT], ValueT], e: ValueT, mapping: Callable[[ActionT, ValueT], ValueT], composition: Callable[[ActionT, ActionT], ActionT], id: ActionT, *, commutative: bool = False) -> None:
        """Initialize an empty persistent implicit weight-balanced tree.

        Args:
            op: Associative operation for aggregates.
            e: Identity element for ``op``.
            mapping: Function that applies a lazy value to an element or aggregate.
            composition: Function that composes two lazy values.
            id: Identity lazy value.
            commutative: If True, skip reverse aggregates; op must be commutative.

        Time Complexity:
            O(1)

        Returns:
            None.
        """
        self.op = op
        self.e = e
        self.mapping = mapping
        self.composition = composition
        self.id = id
        self.val: list[ValueT] = [e]
        self.acc: list[ValueT] = [e]
        self._commutative = commutative
        self._racc: list[ValueT] = [] if commutative else [e]
        self.lazy: list[ActionT] = [id]
        self.left = [0]
        self.right = [0]
        self.cnt = [0]
        self.rev = [False]

    def _new_node(self, value: ValueT) -> int:
        idx = len(self.val)
        self.val.append(value)
        self.acc.append(value)
        if not self._commutative:
            self._racc.append(value)
        self.lazy.append(self.id)
        self.left.append(0)
        self.right.append(0)
        self.cnt.append(1)
        self.rev.append(False)
        return idx

    def _clone(self, node: int) -> int:
        if node == 0:
            return 0
        idx = len(self.val)
        self.val.append(self.val[node])
        self.acc.append(self.acc[node])
        if not self._commutative:
            self._racc.append(self._racc[node])
        self.lazy.append(self.lazy[node])
        self.left.append(self.left[node])
        self.right.append(self.right[node])
        self.cnt.append(self.cnt[node])
        self.rev.append(self.rev[node])
        return idx

    def _apply_mut(self, node: int, lazy_value: ActionT) -> None:
        self.val[node] = self.mapping(lazy_value, self.val[node])
        self.acc[node] = self.mapping(lazy_value, self.acc[node])
        if not self._commutative:
            self._racc[node] = self.mapping(lazy_value, self._racc[node])
        self.lazy[node] = self.composition(lazy_value, self.lazy[node])

    def _toggle_reverse_mut(self, node: int) -> None:
        self.left[node], self.right[node] = self.right[node], self.left[node]
        self.rev[node] ^= True
        if not self._commutative:
            self.acc[node], self._racc[node] = self._racc[node], self.acc[node]

    def _push_mut(self, node: int) -> None:
        if self.rev[node]:
            l = self.left[node]
            if l:
                l = self._clone(l)
                self._toggle_reverse_mut(l)
                self.left[node] = l
            r = self.right[node]
            if r:
                r = self._clone(r)
                self._toggle_reverse_mut(r)
                self.right[node] = r
            self.rev[node] = False
        lazy_value = self.lazy[node]
        if lazy_value != self.id:
            l = self.left[node]
            if l:
                l = self._clone(l)
                self._apply_mut(l, lazy_value)
                self.left[node] = l
            r = self.right[node]
            if r:
                r = self._clone(r)
                self._apply_mut(r, lazy_value)
                self.right[node] = r
            self.lazy[node] = self.id

    def _update(self, node: int) -> int:
        l = self.left[node]
        r = self.right[node]
        self.cnt[node] = self.cnt[l] + self.cnt[r] + 1
        self.acc[node] = self.op(self.op(self.acc[l], self.val[node]), self.acc[r])
        if not self._commutative:
            self._racc[node] = self.op(self.op(self._racc[r], self.val[node]), self._racc[l])
        return node

    def _rotate_left(self, node: int) -> int:
        self._push_mut(node)
        right = self._clone(self.right[node])
        self._push_mut(right)
        self.right[node] = self.left[right]
        self.left[right] = self._update(node)
        return self._update(right)

    def _rotate_right(self, node: int) -> int:
        self._push_mut(node)
        left = self._clone(self.left[node])
        self._push_mut(left)
        self.left[node] = self.right[left]
        self.right[left] = self._update(node)
        return self._update(left)

    def _balance(self, node: int) -> int:
        self._update(node)
        l = self.left[node]
        r = self.right[node]
        if self.cnt[l] > self.cnt[r] * self._DELTA + 1:
            l = self._clone(l)
            self._push_mut(l)
            if self.cnt[self.right[l]] > self.cnt[self.left[l]] * self._GAMMA:
                l = self._rotate_left(l)
            self.left[node] = l
            return self._rotate_right(node)
        if self.cnt[r] > self.cnt[l] * self._DELTA + 1:
            r = self._clone(r)
            self._push_mut(r)
            if self.cnt[self.left[r]] > self.cnt[self.right[r]] * self._GAMMA:
                r = self._rotate_right(r)
            self.right[node] = r
            return self._rotate_left(node)
        return node

    def new_root(self, values: Iterable[ValueT]) -> int:
        """
        Build and return a new root from values.

        Args:
            values: Initial sequence.

        Time Complexity:
            O(n)

        Returns:
            Root of the new version; 0 for an empty sequence.
        """
        arr = list(values)
        if not arr:
            return 0
        root = 0
        created: list[int] = []
        stack = [(0, len(arr), 0, 0)]
        while stack:
            l, r, parent, direction = stack.pop()
            if l >= r:
                continue
            m = (l + r) >> 1
            node = self._new_node(arr[m])
            created.append(node)
            if parent == 0:
                root = node
            elif direction == 0:
                self.left[parent] = node
            else:
                self.right[parent] = node
            stack.append((m + 1, r, node, 1))
            stack.append((l, m, node, 0))
        for node in reversed(created):
            self._update(node)
        return root

    def size(self, root: int) -> int:
        """
        Return the size of a version root.

        Returns:
            Number of elements in the sequence represented by root.

        Time Complexity:
            O(1)

        Args:
            root: Valid root of the source version; 0 denotes an empty sequence.
        """
        return self.cnt[root]

    def split(self, root: int, k: int) -> tuple[int, int]:
        """
        Split ``root`` into the first ``k`` elements and the rest.

        Time Complexity:
            O(log n)

        Args:
            root: Valid root of the source version; 0 denotes an empty sequence.
            k: Number of elements to place in the left result.

        Returns:
            Pair of roots for the prefix of length k and the remaining suffix.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if root == 0:
            return 0, 0
        node = self._clone(root)
        self._push_mut(node)
        left_size = self.cnt[self.left[node]]
        if k <= left_size:
            left_root, right_root = self.split(self.left[node], k)
            self.left[node] = right_root
            return left_root, self._balance(node)
        left_root, right_root = self.split(self.right[node], k - left_size - 1)
        self.right[node] = left_root
        return self._balance(node), right_root

    def _pop_min(self, root: int) -> tuple[int, int]:
        node = self._clone(root)
        self._push_mut(node)
        if self.left[node] == 0:
            right = self.right[node]
            self.right[node] = 0
            self._update(node)
            return node, right
        min_node, rest = self._pop_min(self.left[node])
        self.left[node] = rest
        return min_node, self._balance(node)

    def _join(self, left_root: int, middle: int, right_root: int) -> int:
        if self.cnt[left_root] > (self.cnt[right_root] + 1) * self._DELTA + 1:
            node = self._clone(left_root)
            self._push_mut(node)
            self.right[node] = self._join(self.right[node], middle, right_root)
            return self._balance(node)
        if self.cnt[right_root] > (self.cnt[left_root] + 1) * self._DELTA + 1:
            node = self._clone(right_root)
            self._push_mut(node)
            self.left[node] = self._join(left_root, middle, self.left[node])
            return self._balance(node)
        self.left[middle] = left_root
        self.right[middle] = right_root
        self.rev[middle] = False
        self.lazy[middle] = self.id
        return self._update(middle)

    def merge(self, left_root: int, right_root: int) -> int:
        """
        Concatenate two roots.

        Time Complexity:
            O(log n)

        Args:
            left_root: Root of the first sequence.
            right_root: Root of the sequence to append.

        Returns:
            Root of the concatenated sequence. Both source versions remain valid.
        """
        if left_root == 0:
            return right_root
        if right_root == 0:
            return left_root
        middle, right_root = self._pop_min(right_root)
        return self._join(left_root, middle, right_root)

    def insert(self, root: int, pos: int, value: ValueT) -> int:
        """
        Return a new root with ``value`` inserted at ``pos``.

        Time Complexity:
            O(log n)

        Args:
            root: Valid root of the source version; 0 denotes an empty sequence.
            pos: Zero-based position in the sequence.
            value: Element to insert.

        Returns:
            Root of the updated version. The source remains valid.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= pos <= self.cnt[root]:
            raise IndexError('insert position out of range')
        left_root, right_root = self.split(root, pos)
        return self.merge(self.merge(left_root, self._new_node(value)), right_root)

    def erase(self, root: int, pos: int) -> int:
        """
        Return a new root with the element at ``pos`` removed.

        Time Complexity:
            O(log n)

        Args:
            root: Valid root of the source version; 0 denotes an empty sequence.
            pos: Zero-based position in the sequence.

        Returns:
            Root of the updated version. The source remains valid.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= pos < self.cnt[root]:
            raise IndexError('erase position out of range')
        left_root, rest = self.split(root, pos)
        _, right_root = self.split(rest, 1)
        return self.merge(left_root, right_root)

    def reverse(self, root: int, l: int, r: int) -> int:
        """
        Return a new root with ``[l, r)`` reversed.

        Time Complexity:
            O(log n)

        Args:
            root: Valid root of the source version; 0 denotes an empty sequence.
            l: Inclusive left boundary.
            r: Exclusive right boundary.

        Returns:
            Root of the updated version. The source remains valid.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        if not 0 <= l <= r <= self.cnt[root]:
            raise IndexError('reverse range out of bounds')
        if l == r:
            return root
        left_root, rest = self.split(root, l)
        middle, right_root = self.split(rest, r - l)
        middle = self._clone(middle)
        self._toggle_reverse_mut(middle)
        return self.merge(left_root, self.merge(middle, right_root))

    def range_apply(self, root: int, l: int, r: int, lazy_value: ActionT) -> int:
        """
        Return a new root with a lazy value applied to ``[l, r)``.

        Args:
            root: Valid root of the source version.
            l: Inclusive left boundary.
            r: Exclusive right boundary.
            lazy_value: Update passed to the mapping operation.

        Returns:
            Root of the updated version, or ``root`` if the range is empty.
            The source version remains unchanged.

        Raises:
            IndexError: If ``0 <= l <= r <= size(root)`` does not hold.

        Space Complexity:
            O(log n) additional nodes for a nonempty range.

        Time Complexity:
            O(log n)
        """
        if not 0 <= l <= r <= self.cnt[root]:
            raise IndexError('apply range out of bounds')
        if l == r:
            return root
        left_root, rest = self.split(root, l)
        middle, right_root = self.split(rest, r - l)
        middle = self._clone(middle)
        self._apply_mut(middle, lazy_value)
        return self.merge(left_root, self.merge(middle, right_root))

    def prod(self, root: int, l: int, r: int) -> tuple[ValueT, int]:
        """
        Return the aggregate of ``[l, r)`` and an equivalent restored root.

        Args:
            root: Valid root of the source version.
            l: Inclusive left boundary.
            r: Exclusive right boundary.

        Returns:
            Pair ``(aggregate, restored_root)``. The aggregate follows sequence
            order and is ``e`` for an empty range. Both the source root and the
            restored root represent the original sequence and remain usable.

        Raises:
            IndexError: If ``0 <= l <= r <= size(root)`` does not hold.

        Space Complexity:
            O(log n) additional nodes for a nonempty range.

        Time Complexity:
            O(log n)
        """
        if not 0 <= l <= r <= self.cnt[root]:
            raise IndexError('prod range out of bounds')
        if l == r:
            return self.e, root
        left_root, rest = self.split(root, l)
        middle, right_root = self.split(rest, r - l)
        result = self.acc[middle]
        return result, self.merge(left_root, self.merge(middle, right_root))

    def get(self, root: int, pos: int) -> tuple[ValueT, int]:
        """
        Return the element at ``pos`` and an equivalent restored root.

        Time Complexity:
            O(log n)

        Args:
            root: Valid root of the source version; 0 denotes an empty sequence.
            pos: Zero-based position in the sequence.

        Returns:
            Pair (value, restored_root). Both roots represent the unchanged sequence.

        Raises:
            IndexError: If the position or half-open range is outside the sequence.
        """
        value, root = self.prod(root, pos, pos + 1)
        return value, root

    def iter(self, root: int) -> Iterator[ValueT]:
        """
        Iterate over a version root.

        Time Complexity:
            O(n)

        Args:
            root: Valid root of the source version; 0 denotes an empty sequence.

        Returns:
            Iterator over elements in sequence order.

        Space Complexity:
            O(log n) auxiliary traversal space; no tree nodes are allocated.
        """
        stack = [(root, self.id, False, 0)]
        while stack:
            node, lazy_value, flipped, state = stack.pop()
            if node == 0:
                continue
            if state == 1:
                yield self.mapping(lazy_value, self.val[node])
                continue
            next_lazy = self.composition(lazy_value, self.lazy[node])
            next_flipped = flipped ^ self.rev[node]
            if flipped:
                stack.append((self.left[node], next_lazy, next_flipped, 0))
                stack.append((node, lazy_value, flipped, 1))
                stack.append((self.right[node], next_lazy, next_flipped, 0))
            else:
                stack.append((self.right[node], next_lazy, next_flipped, 0))
                stack.append((node, lazy_value, flipped, 1))
                stack.append((self.left[node], next_lazy, next_flipped, 0))

    def to_list(self, root: int) -> list[ValueT]:
        """
        Return the elements of a version root without allocating tree nodes.

        Time Complexity:
            O(n)

        Args:
            root: Valid root of the source version; 0 denotes an empty sequence.

        Returns:
            Elements of the specified version in sequence order.

        Space Complexity:
            O(n) for the result and O(log n) for traversal; no tree nodes are allocated.
        """
        return list(self.iter(root))
