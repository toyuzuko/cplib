#!/usr/bin/env python3

from __future__ import annotations

from typing import Generic
from collections.abc import Callable, Sequence
from cplib.tools.type import ValueT, ActionT, PointT, PathT


class LinkCutTree(Generic[ValueT]):
    """
    Link-cut tree for dynamic forests with orientation-insensitive path folds.

    This is the standard splay-based link-cut tree supporting ``link``,
    ``cut``, ``reroot``, and path queries on a forest. Each preferred-path
    cluster stores a single aggregate folded with the associative operation
    ``op``. Because only one directional aggregate is maintained, this class is
    intended for path queries whose answer does not depend on traversal
    direction.

    Typical use cases include dynamic tree path sums, xor, min/max, and other
    commutative or orientation-insensitive folds.

    Attributes:
        n: Number of vertices.
        val: Value stored at each vertex.
        sum: Aggregate of the splay subtree rooted at each vertex.
        op: Associative operation for path aggregation.
        ptr: Splay tree pointers and flags packed into one integer array.
            For each vertex ``v``, the following are stored:
            - ptr[v << 2 | 0]: Left child of ``v`` in the splay tree, or ``-1`` if none.
            - ptr[v << 2 | 1]: Right child of ``v`` in the splay tree, or ``-1`` if none.
            - ptr[v << 2 | 2]: Parent of ``v`` in the splay tree, or ``-1`` if none.
            - ptr[v << 2 | 3]: Reversal flag for the preferred path at ``v`` (0 or 1).

    Space Complexity:
        O(n)

    Examples:
        >>> from operator import add
        >>> lct = LinkCutTree(3, 0, add)
        >>> lct.build([1, 2, 3])
        >>> lct.link(1, 0)
        >>> lct.link(2, 1)
        >>> lct.path_prod(0, 2)
        6
        >>> lct.get(1)
        2
        >>> lct.same(0, 2)
        True
        >>> lct.cut_parent(2)
        >>> lct.same(0, 2)
        False
        >>> lct.link(child=1, parent=2)
        >>> lct.root(0)
        2
        >>> lct.cut(0, 1)
        >>> lct.same(0, 1)
        False
    """

    def __init__(self, n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT]) -> None:
        """
        Initialize an empty dynamic forest.

        Args:
            n: Number of vertices.
            e: Identity element of ``op``.
            op: Associative operation for path aggregation.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.n = n
        self.val = [e] * n
        self.sum = [e] * (n + 1)
        self.op = op
        self.ptr = [0 if i % 4 == 3 else -1 for i in range(n << 2)]

    def _update(self, v: int) -> None:
        self.sum[v] = self.op(self.op(self.sum[self.ptr[v << 2 | 0]], self.val[v]), self.sum[self.ptr[v << 2 | 1]])

    def _toggle(self, v: int) -> None:
        if v == -1: return
        self.ptr[v << 2 | 0], self.ptr[v << 2 | 1] = self.ptr[v << 2 | 1], self.ptr[v << 2 | 0]
        self.ptr[v << 2 | 3] ^= 1

    def _push(self, v: int) -> None:
        if v == -1 or not self.ptr[v << 2 | 3]: return
        self._toggle(self.ptr[v << 2 | 0])
        self._toggle(self.ptr[v << 2 | 1])
        self.ptr[v << 2 | 3] = 0

    def _state(self, v: int) -> int:
        p = self.ptr[v << 2 | 2]
        if self.ptr[p << 2 | 0] == v:
            return 1
        elif self.ptr[p << 2 | 1] == v:
            return -1
        else:
            return 0

    def _rotate(self, v: int) -> None:
        if v == -1: return
        s = self._state(v)
        if s == 0: return
        p = self.ptr[v << 2 | 2]
        g = self.ptr[p << 2 | 2]
        t = self._state(p)
        if s == 1:
            r = self.ptr[v << 2 | 1]
            self.ptr[p << 2 | 0] = r
            self.ptr[v << 2 | 1] = p
            if r != -1: self.ptr[r << 2 | 2] = p
        else:
            l = self.ptr[v << 2 | 0]
            self.ptr[p << 2 | 1] = l
            self.ptr[v << 2 | 0] = p
            if l != -1: self.ptr[l << 2 | 2] = p
        self.ptr[p << 2 | 2] = v
        self.ptr[v << 2 | 2] = g
        self._update(p)
        self._update(v)
        if t == 0: return
        if t == 1:
            self.ptr[g << 2 | 0] = v
        else:
            self.ptr[g << 2 | 1] = v

    def _splay(self, v: int) -> None:
        if v == -1: return
        self._push(v)
        while self._state(v):
            s = self._state(v)
            p = self.ptr[v << 2 | 2]
            t = self._state(p)
            if t == 0:
                self._push(p)
                self._push(v)
                self._rotate(v)
            elif s == t:
                self._push(self.ptr[p << 2 | 2])
                self._push(p)
                self._push(v)
                self._rotate(p)
                self._rotate(v)
            else:
                self._push(self.ptr[p << 2 | 2])
                self._push(p)
                self._push(v)
                self._rotate(v)
                self._rotate(v)

    def build(self, arr: list[ValueT]) -> None:
        """
        Initialize vertex values before linking any edges.

        Call this only during initialization, before the first ``link``.
        It does not rebuild aggregates of an existing forest. Use ``set``
        to update vertex values after linking.

        Args:
            arr: Initial values for vertices ``0`` through ``n - 1``.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        for i in range(self.n):
            self.val[i] = arr[i]

    def access(self, v: int) -> None:
        """
        Expose the preferred path from ``v`` to the current root.

        After this call, the splay tree rooted at ``v`` represents exactly the
        path from the represented-tree root to ``v``.

        Args:
            v: Vertex to expose.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        c = v
        r = -1
        while v != -1:
            self._splay(v)
            self.ptr[v << 2 | 1] = r
            self._update(v)
            r = v
            v = self.ptr[v << 2 | 2]
        self._splay(c)

    def link(self, child: int, parent: int) -> None:
        """Reroot the child's tree and attach it under ``parent``.

        The previous root of the parent's component is preserved. Rejected
        links preserve topology, vertex values, and represented roots.

        Args:
            child: Endpoint to make the root of its component before linking.
            parent: Endpoint in a different component to attach under.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints already belong to the same tree.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= child < self.n and 0 <= parent < self.n):
            raise IndexError('vertex index out of range')
        if child == parent:
            raise ValueError('link requires different components')
        self.access(child)
        self.access(parent)
        if self.ptr[child << 2 | 2] != -1:
            raise ValueError('link requires different components')
        self._toggle(child)
        self._push(child)
        self.ptr[child << 2 | 2] = parent
        self.ptr[parent << 2 | 1] = child
        self._update(parent)

    def cut(self, u: int, v: int) -> None:
        """Remove the edge between two vertices, in either endpoint order.

        The resulting components are rooted at ``u`` and ``v`` respectively.
        Rejected cuts preserve topology, values, and represented roots.

        Args:
            u: First endpoint of the edge.
            v: Second endpoint of the edge.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints do not form an existing edge.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        if u == v:
            raise ValueError('edge does not exist')
        self.access(u)
        self.access(v)
        self._splay(u)
        if self.ptr[u << 2 | 1] == v:
            # u is on the exposed root-to-v path. Adjacency leaves no vertex
            # between u and v; check before changing the represented tree.
            self._push(v)
            if self.ptr[v << 2 | 0] != -1:
                raise ValueError('edge does not exist')
            self.ptr[u << 2 | 1] = -1
            self.ptr[v << 2 | 2] = -1
            self._update(u)
            self._toggle(u)
            self._push(u)
        elif self.ptr[u << 2 | 2] == v and self.ptr[u << 2 | 0] == -1:
            # u is a direct virtual child of v after access(v).
            self.ptr[u << 2 | 2] = -1
            self._update(v)
            self._toggle(v)
            self._push(v)
        else:
            raise ValueError('edge does not exist')

    def cut_parent(self, child: int) -> None:
        """Remove the edge between ``child`` and its current parent.

        The parent's component keeps its root; the detached component is
        rooted at ``child``. Rejected cuts preserve topology, values, and roots.

        Args:
            child: Vertex whose parent edge is removed.

        Returns:
            None.

        Raises:
            IndexError: If the vertex index is out of range.
            ValueError: If ``child`` is already a represented-tree root.

        Time Complexity:
            O(log n) amortized.
        """
        if not 0 <= child < self.n:
            raise IndexError('vertex index out of range')
        self.access(child)
        left = self.ptr[child << 2 | 0]
        if left == -1:
            raise ValueError('child must not be a root')
        self.ptr[left << 2 | 2] = -1
        self.ptr[child << 2 | 0] = -1
        self._update(child)

    def reroot(self, v: int) -> None:
        """
        Make ``v`` the root of the represented tree.

        This changes the root of the represented dynamic tree. Auxiliary
        splay-tree roots are managed internally.

        Args:
            v: New root of the tree containing ``v``.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        self._toggle(v)
        self._push(v)

    def set(self, v: int, x: ValueT) -> None:
        """
        Overwrite the value stored at one vertex.

        Args:
            v: Vertex to update.
            x: New value.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        self.val[v] = x
        self._update(v)

    def get(self, v: int) -> ValueT:
        """Return the value stored at one vertex without changing the root.

        Args:
            v: Vertex index.

        Returns:
            Current value stored at ``v``.

        Time Complexity:
            O(1).
        """
        return self.val[v]

    def path_prod(self, u: int, v: int) -> ValueT:
        """
        Return the aggregate on the simple path from ``u`` to ``v``.

        Args:
            u: One endpoint of the query path.
            v: The other endpoint of the query path.

        Returns:
            Aggregate value of the path.

        Time Complexity:
            O(log n) amortized
        """
        self.reroot(u)
        self.access(v)
        return self.sum[v]

    def root(self, v: int) -> int:
        """
        Return the represented-tree root containing ``v``.

        Args:
            v: Vertex whose tree root is queried.

        Returns:
            Root vertex of the represented tree.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        self._push(v)
        while self.ptr[v << 2 | 0] != -1:
            v = self.ptr[v << 2 | 0]
            self._push(v)
        self._splay(v)
        return v

    def same(self, u: int, v: int) -> bool:
        """Return whether two vertices belong to the same tree.

        The represented roots are preserved.

        Args:
            u: First vertex index.
            v: Second vertex index.

        Returns:
            ``True`` if ``u`` and ``v`` are connected, otherwise ``False``.

        Time Complexity:
            O(log n) amortized.
        """
        if u == v:
            return True
        self.access(u)
        self.access(v)
        return self.ptr[u << 2 | 2] != -1

    def parent(self, v: int) -> int:
        """
        Return the parent of ``v`` in the current represented tree.

        Args:
            v: Vertex whose parent is queried.

        Returns:
            Parent vertex, or ``-1`` if ``v`` is a represented-tree root.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        v = self.ptr[v << 2 | 0]
        if v == -1:
            return -1
        self._push(v)
        while self.ptr[v << 2 | 1] != -1:
            v = self.ptr[v << 2 | 1]
            self._push(v)
        self._splay(v)
        return v


class BidirectionalLinkCutTree(Generic[ValueT]):
    """
    Link-cut tree for dynamic forests with orientation-aware path folds.

    This variant keeps both forward and reversed aggregates for every splay
    node and is appropriate when the aggregate depends on the path direction.
    Reversing a preferred path swaps cached forward and backward aggregates, so
    callers do not need to supply a custom reversal callback.

    Typical use cases include affine composition, matrix multiplication, and
    any other non-commutative path query where the answers for ``u -> v`` and
    ``v -> u`` differ.

    Attributes:
        n: Number of vertices.
        val: Value stored at each vertex.
        sum: Forward aggregate of the splay subtree rooted at each vertex.
        rev: Backward aggregate of the splay subtree rooted at each vertex.
        op: Associative operation for path aggregation.
        ptr: Splay tree pointers and flags packed into one integer array.
            For each vertex ``v``, the following are stored:
            - ptr[v << 2 | 0]: Left child of ``v`` in the splay tree, or ``-1`` if none.
            - ptr[v << 2 | 1]: Right child of ``v`` in the splay tree, or ``-1`` if none.
            - ptr[v << 2 | 2]: Parent of ``v`` in the splay tree, or ``-1`` if none.
            - ptr[v << 2 | 3]: Reversal flag for the preferred path at ``v`` (0 or 1).

    Space Complexity:
        O(n)

    Examples:
        >>> def op(left: str, right: str) -> str:
        ...     return left + right
        >>> lct = BidirectionalLinkCutTree(3, '', op)
        >>> lct.build(['a', 'b', 'c'])
        >>> lct.link(1, 0)
        >>> lct.link(2, 1)
        >>> lct.path_prod(0, 2)
        ('abc', 'cba')
    """

    def __init__(self, n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT]) -> None:
        """
        Initialize an empty dynamic forest with directional path aggregates.

        Args:
            n: Number of vertices.
            e: Identity element of ``op``.
            op: Associative operation for forward path composition.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.n = n
        self.val = [e] * n
        self.sum = [e] * (n + 1)
        self.rev = [e] * (n + 1)
        self.op = op
        self.ptr = [0 if i % 4 == 3 else -1 for i in range(n << 2)]

    def _update(self, v: int) -> None:
        left = self.ptr[v << 2 | 0]
        right = self.ptr[v << 2 | 1]
        self.sum[v] = self.op(self.op(self.sum[left], self.val[v]), self.sum[right])
        self.rev[v] = self.op(self.op(self.rev[right], self.val[v]), self.rev[left])

    def _toggle(self, v: int) -> None:
        if v == -1:
            return
        self.sum[v], self.rev[v] = self.rev[v], self.sum[v]
        self.ptr[v << 2 | 0], self.ptr[v << 2 | 1] = self.ptr[v << 2 | 1], self.ptr[v << 2 | 0]
        self.ptr[v << 2 | 3] ^= 1

    def _push(self, v: int) -> None:
        if v == -1 or not self.ptr[v << 2 | 3]:
            return
        self._toggle(self.ptr[v << 2 | 0])
        self._toggle(self.ptr[v << 2 | 1])
        self.ptr[v << 2 | 3] = 0

    def _state(self, v: int) -> int:
        p = self.ptr[v << 2 | 2]
        if self.ptr[p << 2 | 0] == v:
            return 1
        elif self.ptr[p << 2 | 1] == v:
            return -1
        else:
            return 0

    def _rotate(self, v: int) -> None:
        if v == -1:
            return
        s = self._state(v)
        if s == 0:
            return
        p = self.ptr[v << 2 | 2]
        g = self.ptr[p << 2 | 2]
        t = self._state(p)
        if s == 1:
            r = self.ptr[v << 2 | 1]
            self.ptr[p << 2 | 0] = r
            self.ptr[v << 2 | 1] = p
            if r != -1:
                self.ptr[r << 2 | 2] = p
        else:
            l = self.ptr[v << 2 | 0]
            self.ptr[p << 2 | 1] = l
            self.ptr[v << 2 | 0] = p
            if l != -1:
                self.ptr[l << 2 | 2] = p
        self.ptr[p << 2 | 2] = v
        self.ptr[v << 2 | 2] = g
        self._update(p)
        self._update(v)
        if t == 0:
            return
        if t == 1:
            self.ptr[g << 2 | 0] = v
        else:
            self.ptr[g << 2 | 1] = v

    def _splay(self, v: int) -> None:
        if v == -1:
            return
        self._push(v)
        while self._state(v):
            s = self._state(v)
            p = self.ptr[v << 2 | 2]
            t = self._state(p)
            if t == 0:
                self._push(p)
                self._push(v)
                self._rotate(v)
            elif s == t:
                self._push(self.ptr[p << 2 | 2])
                self._push(p)
                self._push(v)
                self._rotate(p)
                self._rotate(v)
            else:
                self._push(self.ptr[p << 2 | 2])
                self._push(p)
                self._push(v)
                self._rotate(v)
                self._rotate(v)

    def build(self, arr: list[ValueT]) -> None:
        """
        Initialize vertex values before linking any edges.

        Call this only during initialization, before the first ``link``.
        It does not rebuild aggregates of an existing forest. Use ``set``
        to update vertex values after linking.

        Args:
            arr: Initial values for vertices ``0`` through ``n - 1``.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        for i in range(self.n):
            self.val[i] = arr[i]
            self.sum[i] = arr[i]
            self.rev[i] = arr[i]

    def access(self, v: int) -> None:
        """
        Expose the preferred path from ``v`` to the current root.

        Args:
            v: Vertex to expose.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        c = v
        r = -1
        while v != -1:
            self._splay(v)
            self.ptr[v << 2 | 1] = r
            self._update(v)
            r = v
            v = self.ptr[v << 2 | 2]
        self._splay(c)

    def link(self, child: int, parent: int) -> None:
        """Reroot the child's tree and attach it under ``parent``.

        The previous root of the parent's component is preserved. Rejected
        links preserve topology, vertex values, and represented roots.

        Args:
            child: Endpoint to make the root of its component before linking.
            parent: Endpoint in a different component to attach under.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints already belong to the same tree.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= child < self.n and 0 <= parent < self.n):
            raise IndexError('vertex index out of range')
        if child == parent:
            raise ValueError('link requires different components')
        self.access(child)
        self.access(parent)
        if self.ptr[child << 2 | 2] != -1:
            raise ValueError('link requires different components')
        self._toggle(child)
        self._push(child)
        self.ptr[child << 2 | 2] = parent
        self.ptr[parent << 2 | 1] = child
        self._update(parent)

    def cut(self, u: int, v: int) -> None:
        """Remove the edge between two vertices, in either endpoint order.

        The resulting components are rooted at ``u`` and ``v`` respectively.
        Rejected cuts preserve topology, values, and represented roots.

        Args:
            u: First endpoint of the edge.
            v: Second endpoint of the edge.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints do not form an existing edge.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        if u == v:
            raise ValueError('edge does not exist')
        self.access(u)
        self.access(v)
        self._splay(u)
        if self.ptr[u << 2 | 1] == v:
            # u is on the exposed root-to-v path. Adjacency leaves no vertex
            # between u and v; check before changing the represented tree.
            self._push(v)
            if self.ptr[v << 2 | 0] != -1:
                raise ValueError('edge does not exist')
            self.ptr[u << 2 | 1] = -1
            self.ptr[v << 2 | 2] = -1
            self._update(u)
            self._toggle(u)
            self._push(u)
        elif self.ptr[u << 2 | 2] == v and self.ptr[u << 2 | 0] == -1:
            # u is a direct virtual child of v after access(v).
            self.ptr[u << 2 | 2] = -1
            self._update(v)
            self._toggle(v)
            self._push(v)
        else:
            raise ValueError('edge does not exist')

    def cut_parent(self, child: int) -> None:
        """Remove the edge between ``child`` and its current parent.

        The parent's component keeps its root; the detached component is
        rooted at ``child``. Rejected cuts preserve topology, values, and roots.

        Args:
            child: Vertex whose parent edge is removed.

        Returns:
            None.

        Raises:
            IndexError: If the vertex index is out of range.
            ValueError: If ``child`` is already a represented-tree root.

        Time Complexity:
            O(log n) amortized.
        """
        if not 0 <= child < self.n:
            raise IndexError('vertex index out of range')
        self.access(child)
        left = self.ptr[child << 2 | 0]
        if left == -1:
            raise ValueError('child must not be a root')
        self.ptr[left << 2 | 2] = -1
        self.ptr[child << 2 | 0] = -1
        self._update(child)

    def reroot(self, v: int) -> None:
        """
        Make ``v`` the root of the represented tree.

        This changes the root of the represented dynamic tree. Auxiliary
        splay-tree roots are managed internally.

        Args:
            v: New root of the tree containing ``v``.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        self._toggle(v)
        self._push(v)

    def set(self, v: int, x: ValueT) -> None:
        """
        Overwrite the value stored at one vertex.

        Args:
            v: Vertex to update.
            x: New value.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        self.val[v] = x
        self._update(v)

    def get(self, v: int) -> ValueT:
        """Return the value stored at one vertex without changing the root.

        Args:
            v: Vertex index.

        Returns:
            Current value stored at ``v``.

        Time Complexity:
            O(1).
        """
        return self.val[v]

    def path_prod(self, u: int, v: int) -> tuple[ValueT, ValueT]:
        """
        Return both directional aggregates on the path between ``u`` and ``v``.

        Args:
            u: One endpoint of the query path.
            v: The other endpoint of the query path.

        Returns:
            ``(forward, backward)`` where ``forward`` is the fold along
            ``u -> v`` and ``backward`` is the fold along ``v -> u``.

        Time Complexity:
            O(log n) amortized
        """
        self.reroot(u)
        self.access(v)
        return (self.sum[v], self.rev[v])

    def root(self, v: int) -> int:
        """
        Return the represented-tree root containing ``v``.

        Args:
            v: Vertex whose tree root is queried.

        Returns:
            Root vertex of the represented tree.

        Time Complexity:
            O(log n) amortized

        """
        self.access(v)
        self._push(v)
        while self.ptr[v << 2 | 0] != -1:
            v = self.ptr[v << 2 | 0]
            self._push(v)
        self._splay(v)
        return v

    def same(self, u: int, v: int) -> bool:
        """Return whether two vertices belong to the same tree.

        The represented roots are preserved.

        Args:
            u: First vertex index.
            v: Second vertex index.

        Returns:
            ``True`` if ``u`` and ``v`` are connected, otherwise ``False``.

        Time Complexity:
            O(log n) amortized.
        """
        if u == v:
            return True
        self.access(u)
        self.access(v)
        return self.ptr[u << 2 | 2] != -1

    def parent(self, v: int) -> int:
        """
        Return the parent of ``v`` in the current represented tree.

        Args:
            v: Vertex whose parent is queried.

        Returns:
            Parent vertex, or ``-1`` if ``v`` is a represented-tree root.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        v = self.ptr[v << 2 | 0]
        if v == -1:
            return -1
        self._push(v)
        while self.ptr[v << 2 | 1] != -1:
            v = self.ptr[v << 2 | 1]
            self._push(v)
        self._splay(v)
        return v


class LazyPathLinkCutTree(Generic[ValueT, ActionT]):
    """
    Link-cut tree with lazy path updates and path queries.

    This structure supports ``link``, ``cut``, ``reroot``, point assignment,
    point queries, path lazy updates, and path aggregate queries. It maintains
    one orientation-insensitive aggregate for each preferred path, so it is
    intended for commutative or otherwise reversal-invariant path folds such as
    sum, xor, min, or max.

    For direction-dependent operations such as affine composition or matrix
    multiplication, use a separate reversible variant rather than this class.

    Space Complexity:
        O(n)
    """

    def __init__(self, n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT], mapping: Callable[[ActionT, ValueT, int], ValueT], composition: Callable[[ActionT, ActionT], ActionT], lazy_identity: ActionT) -> None:
        """
        Initialize an empty dynamic forest.

        Args:
            n: Number of vertices.
            e: Identity element of ``op``.
            op: Associative operation for path aggregation.
            mapping: Lazy action on a path aggregate. The arguments are the
                lazy tag, aggregate value, and path length. A single vertex is
                treated as a path of length ``1``.
            composition: Lazy composition operator. ``composition(f, g)``
                represents applying ``f`` after ``g``.
            lazy_identity: Identity lazy tag.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.n = n
        self.e = e
        self.op = op
        self.mapping = mapping
        self.composition = composition
        self.lazy_identity = lazy_identity

        self.val = [e] * n
        self.sum = [e] * (n + 1)
        self.size = [1] * n + [0]
        self.lazy = [lazy_identity] * (n + 1)
        self.ptr = [0 if i % 4 == 3 else -1 for i in range(n << 2)]

    def _update(self, v: int) -> None:
        left = self.ptr[v << 2 | 0]
        right = self.ptr[v << 2 | 1]
        self.sum[v] = self.op(self.op(self.sum[left], self.val[v]), self.sum[right])
        self.size[v] = self.size[left] + 1 + self.size[right]

    def _all_apply(self, v: int, tag: ActionT) -> None:
        if v == -1:
            return
        self.val[v] = self.mapping(tag, self.val[v], 1)
        self.sum[v] = self.mapping(tag, self.sum[v], self.size[v])
        self.lazy[v] = self.composition(tag, self.lazy[v])

    def _toggle(self, v: int) -> None:
        if v == -1:
            return
        self.ptr[v << 2 | 0], self.ptr[v << 2 | 1] = self.ptr[v << 2 | 1], self.ptr[v << 2 | 0]
        self.ptr[v << 2 | 3] ^= 1

    def _push(self, v: int) -> None:
        if v == -1:
            return
        if self.ptr[v << 2 | 3]:
            self._toggle(self.ptr[v << 2 | 0])
            self._toggle(self.ptr[v << 2 | 1])
            self.ptr[v << 2 | 3] = 0
        if self.lazy[v] != self.lazy_identity:
            self._all_apply(self.ptr[v << 2 | 0], self.lazy[v])
            self._all_apply(self.ptr[v << 2 | 1], self.lazy[v])
            self.lazy[v] = self.lazy_identity

    def _state(self, v: int) -> int:
        p = self.ptr[v << 2 | 2]
        if p == -1:
            return 0
        if self.ptr[p << 2 | 0] == v:
            return 1
        if self.ptr[p << 2 | 1] == v:
            return -1
        return 0

    def _rotate(self, v: int) -> None:
        if v == -1:
            return
        s = self._state(v)
        if s == 0:
            return
        p = self.ptr[v << 2 | 2]
        g = self.ptr[p << 2 | 2]
        t = self._state(p)
        if s == 1:
            r = self.ptr[v << 2 | 1]
            self.ptr[p << 2 | 0] = r
            self.ptr[v << 2 | 1] = p
            if r != -1:
                self.ptr[r << 2 | 2] = p
        else:
            l = self.ptr[v << 2 | 0]
            self.ptr[p << 2 | 1] = l
            self.ptr[v << 2 | 0] = p
            if l != -1:
                self.ptr[l << 2 | 2] = p
        self.ptr[p << 2 | 2] = v
        self.ptr[v << 2 | 2] = g
        if t == 1:
            self.ptr[g << 2 | 0] = v
        elif t == -1:
            self.ptr[g << 2 | 1] = v
        self._update(p)
        self._update(v)

    def _splay(self, v: int) -> None:
        if v == -1:
            return
        stack = [v]
        cur = v
        while self._state(cur):
            cur = self.ptr[cur << 2 | 2]
            stack.append(cur)
        while stack:
            self._push(stack.pop())
        while self._state(v):
            s = self._state(v)
            p = self.ptr[v << 2 | 2]
            t = self._state(p)
            if t == 0:
                self._rotate(v)
            elif s == t:
                self._rotate(p)
                self._rotate(v)
            else:
                self._rotate(v)
                self._rotate(v)

    def build(self, arr: list[ValueT]) -> None:
        """
        Initialize vertex values before linking any edges.

        Call this only during initialization, before the first ``link``.
        It does not rebuild aggregates of an existing forest. Use ``set``
        to update vertex values after linking.

        Args:
            arr: Initial values for vertices ``0`` through ``n - 1``.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        for i in range(self.n):
            self.val[i] = arr[i]
            self.sum[i] = arr[i]
            self.lazy[i] = self.lazy_identity

    def access(self, v: int) -> None:
        """
        Expose the preferred path from ``v`` to the current root.

        Args:
            v: Vertex to expose.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        c = v
        r = -1
        while v != -1:
            self._splay(v)
            self.ptr[v << 2 | 1] = r
            self._update(v)
            r = v
            v = self.ptr[v << 2 | 2]
        self._splay(c)

    def link(self, child: int, parent: int) -> None:
        """Reroot the child's tree and attach it under ``parent``.

        The previous root of the parent's component is preserved. Rejected
        links preserve topology, vertex values, and represented roots.

        Args:
            child: Endpoint to make the root of its component before linking.
            parent: Endpoint in a different component to attach under.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints already belong to the same tree.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= child < self.n and 0 <= parent < self.n):
            raise IndexError('vertex index out of range')
        if child == parent:
            raise ValueError('link requires different components')
        self.access(child)
        self.access(parent)
        if self.ptr[child << 2 | 2] != -1:
            raise ValueError('link requires different components')
        self._toggle(child)
        self._push(child)
        self.ptr[child << 2 | 2] = parent
        self.ptr[parent << 2 | 1] = child
        self._update(parent)

    def cut(self, u: int, v: int) -> None:
        """Remove the edge between two vertices, in either endpoint order.

        The resulting components are rooted at ``u`` and ``v`` respectively.
        Rejected cuts preserve topology, values, and represented roots.

        Args:
            u: First endpoint of the edge.
            v: Second endpoint of the edge.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints do not form an existing edge.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        if u == v:
            raise ValueError('edge does not exist')
        self.access(u)
        self.access(v)
        self._splay(u)
        if self.ptr[u << 2 | 1] == v:
            # u is on the exposed root-to-v path. Adjacency leaves no vertex
            # between u and v; check before changing the represented tree.
            self._push(v)
            if self.ptr[v << 2 | 0] != -1:
                raise ValueError('edge does not exist')
            self.ptr[u << 2 | 1] = -1
            self.ptr[v << 2 | 2] = -1
            self._update(u)
            self._toggle(u)
            self._push(u)
        elif self.ptr[u << 2 | 2] == v and self.ptr[u << 2 | 0] == -1:
            # u is a direct virtual child of v after access(v).
            self.ptr[u << 2 | 2] = -1
            self._update(v)
            self._toggle(v)
            self._push(v)
        else:
            raise ValueError('edge does not exist')

    def cut_parent(self, child: int) -> None:
        """Remove the edge between ``child`` and its current parent.

        The parent's component keeps its root; the detached component is
        rooted at ``child``. Rejected cuts preserve topology, values, and roots.

        Args:
            child: Vertex whose parent edge is removed.

        Returns:
            None.

        Raises:
            IndexError: If the vertex index is out of range.
            ValueError: If ``child`` is already a represented-tree root.

        Time Complexity:
            O(log n) amortized.
        """
        if not 0 <= child < self.n:
            raise IndexError('vertex index out of range')
        self.access(child)
        left = self.ptr[child << 2 | 0]
        if left == -1:
            raise ValueError('child must not be a root')
        self.ptr[left << 2 | 2] = -1
        self.ptr[child << 2 | 0] = -1
        self._update(child)

    def reroot(self, v: int) -> None:
        """
        Make ``v`` the root of the represented tree.

        This changes the root of the represented dynamic tree. Auxiliary
        splay-tree roots are managed internally.

        Args:
            v: New root of the tree containing ``v``.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        self._toggle(v)
        self._push(v)

    def set(self, v: int, x: ValueT) -> None:
        """
        Overwrite the value stored at one vertex.

        Args:
            v: Vertex to update.
            x: New value.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        self.val[v] = x
        self._update(v)

    def get(self, v: int) -> ValueT:
        """
        Return the value stored at one vertex.

        Args:
            v: Vertex to query.

        Returns:
            Current vertex value.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        return self.val[v]

    def path_apply(self, u: int, v: int, tag: ActionT) -> None:
        """
        Apply ``tag`` to every vertex on the path from ``u`` to ``v``.

        Args:
            u: One endpoint of the update path.
            v: The other endpoint of the update path.
            tag: Lazy tag to apply.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.reroot(u)
        self.access(v)
        self._all_apply(v, tag)

    def path_prod(self, u: int, v: int) -> ValueT:
        """
        Return the aggregate on the simple path from ``u`` to ``v``.

        Args:
            u: One endpoint of the query path.
            v: The other endpoint of the query path.

        Returns:
            Aggregate value of the path.

        Time Complexity:
            O(log n) amortized
        """
        self.reroot(u)
        self.access(v)
        return self.sum[v]

    def root(self, v: int) -> int:
        """
        Return the represented-tree root containing ``v``.

        Args:
            v: Vertex whose tree root is queried.

        Returns:
            Root vertex of the represented tree.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        self._push(v)
        while self.ptr[v << 2 | 0] != -1:
            v = self.ptr[v << 2 | 0]
            self._push(v)
        self._splay(v)
        return v

    def same(self, u: int, v: int) -> bool:
        """Return whether two vertices belong to the same tree.

        The represented roots are preserved.

        Args:
            u: First vertex index.
            v: Second vertex index.

        Returns:
            ``True`` if ``u`` and ``v`` are connected, otherwise ``False``.

        Time Complexity:
            O(log n) amortized.
        """
        if u == v:
            return True
        self.access(u)
        self.access(v)
        return self.ptr[u << 2 | 2] != -1

    def parent(self, v: int) -> int:
        """
        Return the parent of ``v`` in the current represented tree.

        Args:
            v: Vertex whose parent is queried.

        Returns:
            Parent vertex, or ``-1`` if ``v`` is a represented-tree root.

        Time Complexity:
            O(log n) amortized
        """
        self.access(v)
        v = self.ptr[v << 2 | 0]
        if v == -1:
            return -1
        self._push(v)
        while self.ptr[v << 2 | 1] != -1:
            v = self.ptr[v << 2 | 1]
            self._push(v)
        self._splay(v)
        return v


class LazySubtreeLinkCutTree(Generic[ValueT, ActionT]):
    """
    Link-cut tree with lazy subtree updates and commutative aggregates.

    This is the direct abstraction of the classic ``subtree_add/subtree_sum``
    link-cut tree implementation that keeps both preferred-path data and
    virtual-child data at every splay node.

    The aggregate side must be a commutative group because ``access`` moves a
    child cluster between the preferred path and the virtual-child pool by
    adding and subtracting aggregates. The lazy side must admit a cancellable
    composition so that a node can recover the difference between its parent's
    accumulated tag and the snapshot already reflected in the node.

    Attributes:
        n: Number of vertices.
        val: Value stored at each vertex.
        size_total: Size of the entire splay subtree rooted at each vertex.
        size_light: Size of the light (virtual-child) subtree at each vertex.
        sum_total: Aggregate of the entire splay subtree rooted at each vertex.
        sum_light: Aggregate of the light (virtual-child) subtree at each vertex.
        lazy_total: Accumulated lazy tag from the root of the represented tree to each vertex.
        lazy_snapshot: Lazy tag snapshot at the last time the vertex was on the preferred path.
        op: Associative operation for path aggregation. It must form a commutative group with ``inv``.
        inv: Inverse on aggregates for moving clusters between preferred path and virtual children.
        mapping: Lazy action on an aggregate value.
                        The first argument is the lazy tag, the second argument is the aggregate value, and the third argument is the size of the aggregate (number of vertices it represents).
        composition: Lazy composition operator.
        lazy_difference: Difference operator on lazy tags for recovering the correct tag at a node.
                        The first argument is the accumulated tag from the parent, and the second argument is the snapshot at the last time the node was on the preferred path.
                        The result is the tag that needs to be applied to the node to reflect all lazy updates from the parent.
        lazy_identity: Identity lazy tag.

    Space Complexity:
        O(n)

    Examples:
        >>> def op(x: int, y: int) -> int:
        ...     return x + y
        >>> def inv(x: int) -> int:
        ...     return -x
        >>> def mapping(f: int, x: int, size: int) -> int:
        ...     return x + f * size
        >>> def composition(f: int, g: int) -> int:
        ...     return f + g
        >>> def lazy_difference(f: int, g: int) -> int:
        ...     return f - g
        >>> lct = LazySubtreeLinkCutTree(3, 0, op, inv, mapping, composition, lazy_difference, 0)
        >>> lct.build([1, 2, 3])
        >>> lct.link(1, 0)
        >>> lct.link(2, 1)
        >>> lct.subtree_aggregate(0)
        6
        >>> lct.subtree_apply(1, 10)
        >>> lct.subtree_aggregate(0)
        26
    """

    def __init__(
        self,
        n: int,
        e: ValueT,
        op: Callable[[ValueT, ValueT], ValueT],
        inv: Callable[[ValueT], ValueT],
        mapping: Callable[[ActionT, ValueT, int], ValueT],
        composition: Callable[[ActionT, ActionT], ActionT],
        lazy_difference: Callable[[ActionT, ActionT], ActionT],
        lazy_identity: ActionT,
    ) -> None:
        """
        Initialize an empty lazy subtree-capable dynamic forest.

        Args:
            n: Number of vertices.
            e: Identity element of the aggregate group.
            op: Aggregate operation.
            inv: Inverse on aggregates.
            mapping: Lazy action on an aggregate. A single vertex is treated
                as an aggregate of size ``1``.
            composition: Lazy composition operator.
            lazy_difference: Difference operator on lazy tags.
            lazy_identity: Identity lazy tag.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.n = n
        self.e = e
        self.op = op
        self.inv = inv
        self.mapping = mapping
        self.composition = composition
        self.lazy_difference = lazy_difference
        self.lazy_identity = lazy_identity

        self.val = [e] * n
        self.size_total = [1] * n + [0]
        self.size_light = [0] * (n + 1)
        self.sum_total = [e] * (n + 1)
        self.sum_light = [e] * (n + 1)
        self.lazy_total = [lazy_identity] * (n + 1)
        self.lazy_snapshot = [lazy_identity] * (n + 1)
        self.ptr = [0 if i % 4 == 3 else -1 for i in range((n + 1) << 2)]

    def _update(self, vertex: int) -> None:
        left = self.ptr[vertex << 2 | 0]
        right = self.ptr[vertex << 2 | 1]
        self._push(left)
        self._push(right)
        self.sum_total[vertex] = self.op(
            self.op(self.op(self.val[vertex], self.sum_light[vertex]), self.sum_total[left]),
            self.sum_total[right],
        )
        self.size_total[vertex] = self.size_light[vertex] + 1 + self.size_total[left] + self.size_total[right]

    def _push(self, vertex: int) -> None:
        if vertex == -1:
            return
        parent = self.ptr[vertex << 2 | 2]
        if parent != -1:
            self._apply_cluster(vertex, self.lazy_difference(self.lazy_total[parent], self.lazy_snapshot[vertex]))
            self.lazy_snapshot[vertex] = self.lazy_total[parent]
        if self.ptr[vertex << 2 | 3]:
            left = self.ptr[vertex << 2 | 0]
            right = self.ptr[vertex << 2 | 1]
            self.ptr[vertex << 2 | 0], self.ptr[vertex << 2 | 1] = right, left
            self.ptr[vertex << 2 | 3] = 0
            self.ptr[left << 2 | 3] ^= 1
            self.ptr[right << 2 | 3] ^= 1

    def _state(self, vertex: int) -> int:
        parent = self.ptr[vertex << 2 | 2]
        if self.ptr[parent << 2 | 0] == vertex:
            return 1
        if self.ptr[parent << 2 | 1] == vertex:
            return -1
        return 0

    def _rotate(self, vertex: int) -> None:
        if vertex == -1:
            return
        state = self._state(vertex)
        if state == 0:
            return
        parent = self.ptr[vertex << 2 | 2]
        grand = self.ptr[parent << 2 | 2]
        parent_state = self._state(parent)
        if state == 1:
            right = self.ptr[vertex << 2 | 1]
            self.ptr[parent << 2 | 0] = right
            self.ptr[vertex << 2 | 1] = parent
            if right != -1:
                self._push(right)
                self.ptr[right << 2 | 2] = parent
                self.lazy_snapshot[right] = self.lazy_total[parent]
        else:
            left = self.ptr[vertex << 2 | 0]
            self.ptr[parent << 2 | 1] = left
            self.ptr[vertex << 2 | 0] = parent
            if left != -1:
                self._push(left)
                self.ptr[left << 2 | 2] = parent
                self.lazy_snapshot[left] = self.lazy_total[parent]
        self.ptr[parent << 2 | 2] = vertex
        self.ptr[vertex << 2 | 2] = grand
        self.lazy_snapshot[parent] = self.lazy_total[vertex]
        if grand != -1:
            if parent_state == 1:
                self.ptr[grand << 2 | 0] = vertex
            elif parent_state == -1:
                self.ptr[grand << 2 | 1] = vertex
            self.lazy_snapshot[vertex] = self.lazy_total[grand]
        self._update(parent)
        self._update(vertex)

    def _splay(self, vertex: int) -> None:
        if vertex == -1:
            return
        self._push(vertex)
        while self._state(vertex):
            state = self._state(vertex)
            parent = self.ptr[vertex << 2 | 2]
            grand = self.ptr[parent << 2 | 2]
            parent_state = self._state(parent)
            if parent_state == 0:
                self._push(parent)
                self._push(vertex)
                self._rotate(vertex)
            elif state == parent_state:
                self._push(grand)
                self._push(parent)
                self._push(vertex)
                self._rotate(parent)
                self._rotate(vertex)
            else:
                self._push(grand)
                self._push(parent)
                self._push(vertex)
                self._rotate(vertex)
                self._rotate(vertex)

    def build(self, arr: list[ValueT]) -> None:
        """
        Initialize vertex values before linking any edges.

        Call this only during initialization, before the first ``link``.
        It does not rebuild aggregates of an existing forest. Use ``set``
        to update vertex values after linking.

        Args:
            arr: Sequence used to build the structure.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        for i, value in enumerate(arr):
            self.val[i] = value
            self.sum_total[i] = value
            self.lazy_total[i] = self.lazy_identity
            self.lazy_snapshot[i] = self.lazy_identity

    def access(self, vertex: int) -> None:
        """
        Expose the preferred path from ``vertex`` to the current root.

        Args:
            vertex: Vertex index.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        current = vertex
        last = -1
        while current != -1:
            self._splay(current)
            right = self.ptr[current << 2 | 1]
            if right != -1:
                self._push(right)
                self.size_light[current] += self.size_total[right]
                self.sum_light[current] = self.op(self.sum_light[current], self.sum_total[right])
            self.ptr[current << 2 | 1] = last
            if last != -1:
                self._push(last)
                self.size_light[current] -= self.size_total[last]
                self.sum_light[current] = self.op(self.sum_light[current], self.inv(self.sum_total[last]))
            self._update(current)
            last = current
            current = self.ptr[current << 2 | 2]
        self._splay(vertex)

    def reroot(self, vertex: int) -> None:
        """
        Make ``vertex`` the root of the represented tree.

        This changes the root of the represented dynamic tree. Auxiliary
        splay-tree roots are managed internally.

        Args:
            vertex: Vertex index.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        self.ptr[vertex << 2 | 3] ^= 1
        self._push(vertex)

    def link(self, child: int, parent: int) -> None:
        """Reroot the child's tree and attach it under ``parent``.

        The previous root of the parent's component is preserved. Rejected
        links preserve topology, vertex values, and represented roots.

        Args:
            child: Endpoint to make the root of its component before linking.
            parent: Endpoint in a different component to attach under.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints already belong to the same tree.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= child < self.n and 0 <= parent < self.n):
            raise IndexError('vertex index out of range')
        if child == parent:
            raise ValueError('link requires different components')
        self.access(child)
        self.access(parent)
        if self.ptr[child << 2 | 2] != -1:
            raise ValueError('link requires different components')
        self.ptr[child << 2 | 3] ^= 1
        self._push(child)
        self.ptr[child << 2 | 2] = parent
        self.ptr[parent << 2 | 1] = child
        self.lazy_snapshot[child] = self.lazy_total[parent]
        self._update(parent)

    def cut(self, u: int, v: int) -> None:
        """Remove the edge between two vertices, in either endpoint order.

        The resulting components are rooted at ``u`` and ``v`` respectively.
        Rejected cuts preserve topology, values, and represented roots.

        Args:
            u: First endpoint of the edge.
            v: Second endpoint of the edge.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints do not form an existing edge.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        if u == v:
            raise ValueError('edge does not exist')
        self.access(u)
        self.access(v)
        self._splay(u)
        if self.ptr[u << 2 | 1] == v:
            # u is on the exposed root-to-v path. Adjacency leaves no vertex
            # between u and v; check before changing the represented tree.
            self._push(v)
            if self.ptr[v << 2 | 0] != -1:
                raise ValueError('edge does not exist')
            self.ptr[u << 2 | 1] = -1
            self.ptr[v << 2 | 2] = -1
            self._update(u)
            self.ptr[u << 2 | 3] ^= 1
            self._push(u)
        elif self.ptr[u << 2 | 2] == v and self.ptr[u << 2 | 0] == -1:
            # u is a direct virtual child of v after access(v).
            self.size_light[v] -= self.size_total[u]
            self.sum_light[v] = self.op(self.sum_light[v], self.inv(self.sum_total[u]))
            self.ptr[u << 2 | 2] = -1
            self._update(v)
            self.ptr[v << 2 | 3] ^= 1
            self._push(v)
        else:
            raise ValueError('edge does not exist')

    def cut_parent(self, child: int) -> None:
        """Remove the edge between ``child`` and its current parent.

        The parent's component keeps its root; the detached component is
        rooted at ``child``. Rejected cuts preserve topology, values, and roots.

        Args:
            child: Vertex whose parent edge is removed.

        Returns:
            None.

        Raises:
            IndexError: If the vertex index is out of range.
            ValueError: If ``child`` is already a represented-tree root.

        Time Complexity:
            O(log n) amortized.
        """
        if not 0 <= child < self.n:
            raise IndexError('vertex index out of range')
        self.access(child)
        left = self.ptr[child << 2 | 0]
        if left == -1:
            raise ValueError('child must not be a root')
        self.ptr[left << 2 | 2] = -1
        self.ptr[child << 2 | 0] = -1
        self._update(child)

    def set(self, vertex: int, value: ValueT) -> None:
        """
        Overwrite the value of one vertex.

        Args:
            vertex: Vertex index.
            value: Stored value or update value.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        self.val[vertex] = value
        self._update(vertex)

    def get(self, vertex: int) -> ValueT:
        """
        Return the current value of one vertex.

        Args:
            vertex: Vertex index.

        Returns:
            Current value stored at ``vertex``.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        return self.val[vertex]

    def root(self, vertex: int) -> int:
        """
        Return the root of the tree containing ``vertex``.

        Args:
            vertex: Vertex index.

        Returns:
            Root vertex of the tree containing ``vertex``.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        self._push(vertex)
        while self.ptr[vertex << 2 | 0] != -1:
            vertex = self.ptr[vertex << 2 | 0]
            self._push(vertex)
        self._splay(vertex)
        return vertex

    def same(self, u: int, v: int) -> bool:
        """Return whether two vertices belong to the same tree.

        The represented roots are preserved.

        Args:
            u: First vertex index.
            v: Second vertex index.

        Returns:
            ``True`` if ``u`` and ``v`` are connected, otherwise ``False``.

        Time Complexity:
            O(log n) amortized.
        """
        if u == v:
            return True
        self.access(u)
        self.access(v)
        return self.ptr[u << 2 | 2] != -1

    def parent(self, vertex: int) -> int:
        """
        Return the parent of ``vertex`` or ``-1`` if it is a root.

        Args:
            vertex: Vertex index.

        Returns:
            Parent vertex, or ``-1`` if ``vertex`` is a root.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        vertex = self.ptr[vertex << 2 | 0]
        if vertex == -1:
            return -1
        self._push(vertex)
        while self.ptr[vertex << 2 | 1] != -1:
            vertex = self.ptr[vertex << 2 | 1]
            self._push(vertex)
        self._splay(vertex)
        return vertex

    def _apply_cluster(self, vertex: int, tag: ActionT) -> None:
        self.val[vertex] = self.mapping(tag, self.val[vertex], 1)
        self.sum_total[vertex] = self.mapping(tag, self.sum_total[vertex], self.size_total[vertex])
        self.sum_light[vertex] = self.mapping(tag, self.sum_light[vertex], self.size_light[vertex])
        self.lazy_total[vertex] = self.composition(tag, self.lazy_total[vertex])

    def tree_apply(self, vertex: int, tag: ActionT) -> None:
        """
        Apply ``tag`` to every vertex in the tree containing ``vertex``.

        The represented root is preserved. No prior ``access`` or ``reroot``
        call is required.

        Args:
            vertex: Any vertex in the target tree.
            tag: Lazy action to apply to all vertex values in that tree.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        self._apply_cluster(vertex, tag)

    def tree_aggregate(self, vertex: int) -> ValueT:
        """
        Return the aggregate of the tree containing ``vertex``.

        The represented root is preserved. No prior ``access`` or ``reroot``
        call is required.

        Args:
            vertex: Any vertex in the target tree.

        Returns:
            Aggregate of all vertex values in that tree.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        return self.sum_total[vertex]

    def subtree_apply(self, vertex: int, tag: ActionT, root: int | None = None) -> None:
        """
        Apply ``tag`` to the subtree rooted at ``vertex``.

        Args:
            vertex: Vertex index.
            tag: Lazy action to apply to each vertex in the subtree.
            root: Optional vertex in the same tree to make the represented
                root before the update. This root change persists. If omitted,
                the current represented root is used.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        if root is not None:
            self.reroot(root)
        parent = self.parent(vertex)
        if parent == -1:
            self._apply_cluster(vertex, tag)
            return
        self.cut_parent(vertex)
        self._apply_cluster(vertex, tag)
        self.link(vertex, parent)

    def subtree_aggregate(self, vertex: int, root: int | None = None) -> ValueT:
        """
        Return the aggregate over the subtree rooted at ``vertex``.

        Args:
            vertex: Vertex index.
            root: Optional vertex in the same tree to make the represented
                root before the query. This root change persists. If omitted,
                the current represented root is used.

        Returns:
            Aggregate over the requested subtree.

        Time Complexity:
            O(log n) amortized
        """
        if root is not None:
            self.reroot(root)
        parent = self.parent(vertex)
        if parent == -1:
            return self.sum_total[vertex]
        self.cut_parent(vertex)
        result = self.sum_total[vertex]
        self.link(vertex, parent)
        return result


class DynamicTreeAddTreeSum:
    """
    Dynamic tree for subtree-add and subtree-sum queries.

    This is the integer-add / integer-sum specialization of
    :class:`LazySubtreeLinkCutTree`.

    Space Complexity:
        O(n)
    """

    def __init__(self, n: int) -> None:
        """
        Initialize the integer add/sum specialization.

        Args:
            n: Number of vertices.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self._tree = LazySubtreeLinkCutTree[int, int](
            n,
            0,
            lambda a, b: a + b,
            lambda x: -x,
            lambda f, s, sz: s + f * sz,
            lambda f, g: f + g,
            lambda f, g: f - g,
            0,
        )

    def build(self, arr: list[int]) -> None:
        """
        Initialize vertex values before linking any edges.

        Call this only during initialization, before the first ``link``.
        It does not rebuild aggregates of an existing forest. Use ``set``
        to update vertex values after linking.

        Args:
            arr: Sequence used to build the structure.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self._tree.build(arr)

    def access(self, v: int) -> None:
        """
        Expose the preferred path from ``v`` to the current root.

        Args:
            v: Second vertex or endpoint index.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self._tree.access(v)

    def link(self, child: int, parent: int) -> None:
        """Reroot the child's tree and attach it under ``parent``.

        The previous root of the parent's component is preserved. Rejected
        links preserve topology, vertex values, and represented roots.

        Args:
            child: Endpoint to make the root of its component before linking.
            parent: Endpoint in a different component to attach under.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints already belong to the same tree.

        Time Complexity:
            O(log n) amortized.
        """
        self._tree.link(child, parent)

    def cut(self, u: int, v: int) -> None:
        """Remove the edge between two vertices, in either endpoint order.

        The resulting components are rooted at ``u`` and ``v`` respectively.
        Rejected cuts preserve topology, values, and represented roots.

        Args:
            u: First endpoint of the edge.
            v: Second endpoint of the edge.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints do not form an existing edge.

        Time Complexity:
            O(log n) amortized.
        """
        self._tree.cut(u, v)

    def cut_parent(self, child: int) -> None:
        """Remove the edge between ``child`` and its current parent.

        The parent's component keeps its root; the detached component is
        rooted at ``child``. Rejected cuts preserve topology, values, and roots.

        Args:
            child: Vertex whose parent edge is removed.

        Returns:
            None.

        Raises:
            IndexError: If the vertex index is out of range.
            ValueError: If ``child`` is already a represented-tree root.

        Time Complexity:
            O(log n) amortized.
        """
        self._tree.cut_parent(child)

    def reroot(self, vertex: int) -> None:
        """
        Make ``vertex`` the root of the represented tree.

        This changes the root of the represented dynamic tree. Auxiliary
        splay-tree roots are managed internally.

        Args:
            vertex: Vertex index.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self._tree.reroot(vertex)

    def root(self, vertex: int) -> int:
        """
        Return the root of the tree containing ``vertex``.

        Args:
            vertex: Vertex index.

        Returns:
            Root vertex of the tree containing ``vertex``.

        Time Complexity:
            O(log n) amortized
        """
        return self._tree.root(vertex)

    def same(self, u: int, v: int) -> bool:
        """Return whether two vertices belong to the same tree.

        The represented roots are preserved.

        Args:
            u: First vertex index.
            v: Second vertex index.

        Returns:
            ``True`` if ``u`` and ``v`` are connected, otherwise ``False``.

        Time Complexity:
            O(log n) amortized.
        """
        return self._tree.same(u, v)

    def parent(self, vertex: int) -> int:
        """
        Return the parent of ``vertex`` or ``-1`` if it is a root.

        Args:
            vertex: Vertex index.

        Returns:
            Parent vertex, or ``-1`` if ``vertex`` is a root.

        Time Complexity:
            O(log n) amortized
        """
        return self._tree.parent(vertex)

    def set(self, vertex: int, value: int) -> None:
        """
        Overwrite the value of one vertex.

        Args:
            vertex: Vertex index.
            value: Stored value or update value.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self._tree.set(vertex, value)

    def get(self, vertex: int) -> int:
        """
        Return the current value of one vertex.

        Args:
            vertex: Vertex index.

        Returns:
            Current value stored at ``vertex``.

        Time Complexity:
            O(log n) amortized
        """
        return self._tree.get(vertex)

    def subtree_add(self, vertex: int, value: int, root: int | None = None) -> None:
        """
        Add ``value`` to every vertex in the subtree rooted at ``vertex``.

        Args:
            vertex: Vertex index.
            value: Amount to add to each vertex in the subtree.
            root: Optional vertex in the same tree to make the represented
                root before the update. This root change persists. If omitted,
                the current represented root is used.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self._tree.subtree_apply(vertex, value, root)

    def subtree_sum(self, vertex: int, root: int | None = None) -> int:
        """
        Return the sum over the subtree rooted at ``vertex``.

        Args:
            vertex: Vertex index.
            root: Optional vertex in the same tree to make the represented
                root before the query. This root change persists. If omitted,
                the current represented root is used.

        Returns:
            Sum over the requested subtree.

        Time Complexity:
            O(log n) amortized
        """
        return self._tree.subtree_aggregate(vertex, root)

    def tree_add(self, vertex: int, value: int) -> None:
        """
        Add ``value`` to every vertex in the tree containing ``vertex``.

        The represented root is preserved; no preparatory call is required.

        Args:
            vertex: Any vertex in the target tree.
            value: Amount to add to each vertex in that tree.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self._tree.tree_apply(vertex, value)

    def tree_sum(self, vertex: int) -> int:
        """
        Return the sum of all vertex values in the tree containing ``vertex``.

        The represented root is preserved; no preparatory call is required.

        Args:
            vertex: Any vertex in the target tree.

        Returns:
            Sum of all vertex values in that tree.

        Time Complexity:
            O(log n) amortized
        """
        return self._tree.tree_aggregate(vertex)


class RerootingLinkCutTree(Generic[ValueT, PointT, PathT]):
    """
    Link-cut tree for dynamic rerooting-style tree aggregation.

    Here, "rerooting" refers to tree DP evaluated under changes of the
    represented root, not merely the root-changing operation supported by
    ordinary link-cut trees. The structure maintains off-path branch
    contributions and supports both whole-tree and subtree DP queries.

    This data structure maintains a forest of rooted or unrooted trees under
    dynamic edge updates. It supports linking two trees, cutting an existing
    edge, changing the represented root, and querying aggregates on a whole
    rerooted tree, an exposed path cluster including its attached branches,
    or a rooted subtree.

    The implementation is designed for rerooting-style dynamic programming on
    trees. Instead of fixing a concrete aggregate such as sum, maximum, or
    subtree size, it receives the algebraic operations as callbacks. This makes
    the structure reusable for many tree DP problems, provided that the DP can
    be decomposed into:

    - a `Point` aggregate for virtual children or light subtrees;
    - a `Path` aggregate for preferred-path clusters;
    - `add_vertex`, which attaches the value of a vertex to a point aggregate;
    - `add_edge`, which converts a path aggregate into a contribution to a
      parent-side point aggregate;
    - `rake`, which merges point aggregates;
    - `point_inv`, which removes a point contribution from a point aggregate;
    - `compress`, which concatenates path aggregates.

    The `Point` aggregate must form a commutative group under `rake`, with
    identity `point_identity` and inverse `point_inv`, so contributions can be
    added and removed in any order during `access`. The `Path` aggregate
    must be associative under `compress`: splay rotations change the grouping
    of path vertices, but preserve their order.

    Vertices are identified by integer indices from `0` to `n - 1`. The value
    stored at each vertex is kept in `info`, and may be updated by `set`.

    Attributes:
        n: Number of vertices.
        info: Value stored at each vertex.
        point_identity: Identity value for point aggregates.
        add_vertex: Attaches a vertex value to a point aggregate.
        add_edge: Converts a path aggregate into a point contribution.
        rake: Merges point aggregates.
        point_inv: Inverse on point aggregates for removing contributions during `access`.
        compress: Merges path aggregates for maintaining preferred-path data.

    Examples:
        The following example maintains the sum of vertex weights in a dynamic
        tree. In this simple case, both `Point` and `Path` are represented by
        integers.

        >>> weights = [1, 2, 3]
        >>> lct = RerootingLinkCutTree(
        ...     weights,
        ...     point_identity=0,
        ...     add_vertex=lambda point, info: point + info,
        ...     add_edge=lambda path: path,
        ...     rake=lambda a, b: a + b,
        ...     point_inv=lambda x: -x,
        ...     compress=lambda a, b: a + b,
        ... )
        >>> lct.link(1, 0)
        >>> lct.link(2, 1)
        >>> lct.tree_value(0)
        6
        >>> lct.path_cluster_value(0, 2)
        6
        >>> lct.path_cluster_value(0, 1)
        6
        >>> lct.set(1, 10)
        >>> lct.tree_value(2)
        14

        Even ``path_cluster_value(0, 1)`` includes vertex ``2`` through its branch
        contribution. Use a path-only link-cut tree for ordinary path sums.

    Space Complexity:
        O(n)
    """

    def __init__(
        self,
        values: Sequence[ValueT],
        point_identity: PointT,
        add_vertex: Callable[[PointT, ValueT], PathT],
        add_edge: Callable[[PathT], PointT],
        rake: Callable[[PointT, PointT], PointT],
        point_inv: Callable[[PointT], PointT],
        compress: Callable[[PathT, PathT], PathT],
    ) -> None:
        """
        Initialize the rerooting link-cut tree.

        Args:
            values: Initial information values.
            point_identity: Identity value for point aggregates.
            add_vertex: Attaches a vertex value to an aggregate.
            add_edge: Converts a path aggregate into an edge contribution.
            rake: Commutative group operation on light-subtree aggregates.
            point_inv: Inverse under ``rake``.
            compress: Merges path aggregates.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.n = len(values)
        self.info = list(values)
        self.point_identity = point_identity
        self.add_vertex = add_vertex
        self.add_edge = add_edge
        self.rake = rake
        self.point_inv = point_inv
        self.compress = compress

        self.left = [-1] * self.n
        self.right = [-1] * self.n
        self.parent = [-1] * self.n
        self.rev = [0] * self.n
        self.point = [point_identity] * self.n
        self.sum: list[PathT] = [self.add_vertex(point_identity, value) for value in values]
        self.mus: list[PathT] = self.sum[:]

    def _is_root(self, vertex: int) -> bool:
        parent = self.parent[vertex]
        return parent == -1 or (self.left[parent] != vertex and self.right[parent] != vertex)

    def _toggle(self, vertex: int) -> None:
        if vertex == -1:
            return
        self.left[vertex], self.right[vertex] = self.right[vertex], self.left[vertex]
        self.sum[vertex], self.mus[vertex] = self.mus[vertex], self.sum[vertex]
        self.rev[vertex] ^= 1

    def _push(self, vertex: int) -> None:
        if vertex == -1 or not self.rev[vertex]:
            return
        self._toggle(self.left[vertex])
        self._toggle(self.right[vertex])
        self.rev[vertex] = 0

    def _update(self, vertex: int) -> None:
        path = self.add_vertex(self.point[vertex], self.info[vertex])
        rev_path = path
        left = self.left[vertex]
        right = self.right[vertex]
        if left != -1:
            path = self.compress(self.sum[left], path)
            rev_path = self.compress(rev_path, self.mus[left])
        if right != -1:
            path = self.compress(path, self.sum[right])
            rev_path = self.compress(self.mus[right], rev_path)
        self.sum[vertex] = path
        self.mus[vertex] = rev_path

    def _rotate(self, vertex: int) -> None:
        parent = self.parent[vertex]
        grand = self.parent[parent]
        if self.left[parent] == vertex:
            child = self.right[vertex]
            self.right[vertex] = parent
            self.left[parent] = child
            if child != -1:
                self.parent[child] = parent
        else:
            child = self.left[vertex]
            self.left[vertex] = parent
            self.right[parent] = child
            if child != -1:
                self.parent[child] = parent
        self.parent[parent] = vertex
        self.parent[vertex] = grand
        if grand != -1:
            if self.left[grand] == parent:
                self.left[grand] = vertex
            elif self.right[grand] == parent:
                self.right[grand] = vertex
        # Rotation preserves the whole subtree's forward and reverse folds.
        # Only the demoted parent's subtree needs to be recomputed.
        self.sum[vertex] = self.sum[parent]
        self.mus[vertex] = self.mus[parent]
        self._update(parent)

    def _splay(self, vertex: int) -> None:
        stack = [vertex]
        current = vertex
        while not self._is_root(current):
            current = self.parent[current]
            stack.append(current)
        while stack:
            self._push(stack.pop())
        while not self._is_root(vertex):
            parent = self.parent[vertex]
            grand = self.parent[parent]
            if not self._is_root(parent):
                if (self.left[parent] == vertex) == (self.left[grand] == parent):
                    self._rotate(parent)
                else:
                    self._rotate(vertex)
            self._rotate(vertex)

    def access(self, vertex: int) -> int:
        """
        Expose the preferred path from ``vertex`` to the current root.

        The represented-tree root is preserved; ``vertex`` becomes the root
        of the auxiliary splay tree representing the exposed path.

        Args:
            vertex: Vertex index.

        Returns:
            The last vertex processed while joining preferred paths. This
            depends on the previous preferred paths and need not be the
            represented-tree root.

        Time Complexity:
            O(log n) amortized
        """
        last = -1
        current = vertex
        while current != -1:
            self._splay(current)
            right = self.right[current]
            if right != -1:
                self.point[current] = self.rake(self.point[current], self.add_edge(self.sum[right]))
            self.right[current] = last
            if last != -1:
                self.point[current] = self.rake(
                    self.point[current],
                    self.point_inv(self.add_edge(self.sum[last])),
                )
                self.parent[last] = current
            self._update(current)
            last = current
            current = self.parent[current]
        self._splay(vertex)
        return last

    def reroot(self, vertex: int) -> None:
        """
        Make ``vertex`` the root of the represented tree.

        This changes the root of the represented dynamic tree. Auxiliary
        splay-tree roots are managed internally.

        Args:
            vertex: Vertex index.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        self._toggle(vertex)
        self._push(vertex)

    def link(self, child: int, parent: int) -> None:
        """Reroot the child's tree and attach it under ``parent``.

        The previous root of the parent's component is preserved. Rejected
        links preserve topology, vertex values, and represented roots.

        Args:
            child: Endpoint to make the root of its component before linking.
            parent: Endpoint in a different component to attach under.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints already belong to the same tree.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= child < self.n and 0 <= parent < self.n):
            raise IndexError('vertex index out of range')
        if child == parent:
            raise ValueError('link requires different components')
        self.access(child)
        self.access(parent)
        if self.parent[child] != -1:
            raise ValueError('link requires different components')
        self._toggle(child)
        self._push(child)
        self.parent[child] = parent
        self.right[parent] = child
        self._update(parent)

    def cut(self, u: int, v: int) -> None:
        """Remove the edge between two vertices, in either endpoint order.

        The resulting components are rooted at ``u`` and ``v`` respectively.
        Rejected cuts preserve topology, values, and represented roots.

        Args:
            u: First endpoint of the edge.
            v: Second endpoint of the edge.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints do not form an existing edge.

        Time Complexity:
            O(log n) amortized.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        if u == v:
            raise ValueError('edge does not exist')
        self.access(u)
        self.access(v)
        self._splay(u)
        if self.right[u] == v:
            # u is on the exposed root-to-v path. Adjacency leaves no vertex
            # between u and v; check before changing the represented tree.
            self._push(v)
            if self.left[v] != -1:
                raise ValueError('edge does not exist')
            self.right[u] = -1
            self.parent[v] = -1
            self._update(u)
            self._toggle(u)
            self._push(u)
        elif self.parent[u] == v and self.left[u] == -1:
            # u is a direct virtual child of v after access(v).
            self.point[v] = self.rake(self.point[v], self.point_inv(self.add_edge(self.sum[u])))
            self.parent[u] = -1
            self._update(v)
            self._toggle(v)
            self._push(v)
        else:
            raise ValueError('edge does not exist')

    def cut_parent(self, child: int) -> None:
        """Remove the edge between ``child`` and its current parent.

        The parent's component keeps its root; the detached component is
        rooted at ``child``. Rejected cuts preserve topology, values, and roots.

        Args:
            child: Vertex whose parent edge is removed.

        Returns:
            None.

        Raises:
            IndexError: If the vertex index is out of range.
            ValueError: If ``child`` is already a represented-tree root.

        Time Complexity:
            O(log n) amortized.
        """
        if not 0 <= child < self.n:
            raise IndexError('vertex index out of range')
        self.access(child)
        left = self.left[child]
        if left == -1:
            raise ValueError('child must not be a root')
        self.parent[left] = -1
        self.left[child] = -1
        self._update(child)

    def same(self, u: int, v: int) -> bool:
        """
        Return whether ``u`` and ``v`` lie in the same tree.

        The represented roots are preserved.

        Args:
            u: First vertex or endpoint index.
            v: Second vertex or endpoint index.

        Returns:
            ``True`` if ``u`` and ``v`` are connected, otherwise ``False``.

        Time Complexity:
            O(log n) amortized
        """
        if u == v:
            return True
        self.access(u)
        self.access(v)
        return self.parent[u] != -1

    def set(self, vertex: int, value: ValueT) -> None:
        """
        Overwrite the stored information at ``vertex``.

        Args:
            vertex: Vertex index.
            value: Vertex or edge information value.

        Returns:
            None.

        Time Complexity:
            O(log n) amortized
        """
        self.access(vertex)
        self.info[vertex] = value
        self._update(vertex)

    def get(self, vertex: int) -> ValueT:
        """
        Return the stored information at ``vertex``.

        Args:
            vertex: Vertex index.

        Returns:
            Current information value of ``vertex``.

        Time Complexity:
            O(1)
        """
        return self.info[vertex]

    def tree_value(self, vertex: int) -> PathT:
        """
        Return the rerooted aggregate when rooting at ``vertex``.

        The represented root becomes ``vertex`` and remains so after the query.

        Args:
            vertex: Vertex index.

        Returns:
            Aggregate of the whole tree rerooted at ``vertex``.

        Time Complexity:
            O(log n) amortized
        """
        self.reroot(vertex)
        return self.sum[vertex]

    def path_cluster_value(self, u: int, v: int) -> PathT:
        """
        Return the exposed path-cluster aggregate on ``u -> v``.

        Each path vertex includes the ``rake`` aggregate of branches outside
        the path, passed through ``add_vertex``. These values are combined in
        path order with ``compress``. The result therefore includes off-path
        DP contributions; it is not a fold of only the stored path values.

        The represented root becomes ``u`` and remains so after the query.

        Args:
            u: Start vertex and new represented root.
            v: End vertex, which must be in the same tree as ``u``.

        Returns:
            Path-cluster DP value including all attached branch contributions.

        Time Complexity:
            O(log n) amortized
        """
        self.reroot(u)
        self.access(v)
        return self.sum[v]

    def subtree_value(self, vertex: int, root: int | None = None) -> PathT:
        """
        Return the aggregate of the subtree rooted at ``vertex``.

        Args:
            vertex: Vertex index.
            root: Optional vertex in the same tree to make the represented
                root before the query. This root change persists. If omitted,
                the current represented root is used.

        Returns:
            Aggregate of the requested subtree.

        Time Complexity:
            O(log n) amortized
        """
        if root is not None:
            self.reroot(root)
        self.access(vertex)
        left = self.left[vertex]
        self.left[vertex] = -1
        self._update(vertex)
        result = self.sum[vertex]
        self.left[vertex] = left
        self._update(vertex)
        return result


class RerootingLinkCutTreeWithEdges(Generic[ValueT, PointT, PathT]):
    """
    Rerooting link-cut forest with values on vertices and edges.

    `RerootingLinkCutTree` stores information on vertices. This helper
    adapts that representation to problems where values are naturally stored
    on edges. Each registered edge is replaced by one additional vertex, so an
    undirected edge `u - v` becomes the two-edge path:

        u - edge_node - v

    Original vertices keep their indices `0 .. n - 1`. Edge-nodes are assigned
    indices starting from `n`, in the same order as the registered edge ids.
    After `build()` has been called, `vs` contains the original vertex ids and
    `es` contains the corresponding edge-node ids.

    This representation is useful for dynamic-tree problems where both
    vertices and edges need to participate in the same aggregation framework,
    or where the underlying link-cut tree implementation only supports
    vertex-associated values.

    Initialize every original vertex with ``set_vertex()`` and register the
    initial forest with ``add_edge()`` before calling ``build()`` once.
    ``set_vertex`` and ``set_edge`` also update values after construction;
    ``get_vertex`` and ``get_edge`` retrieve them in either phase.

    The vertex count and registered edge slots are fixed after construction.
    ``cut_edge`` detaches an edge, and ``link_edge`` reconnects that same slot
    between any two different components. Edge IDs and payloads survive cuts.
    A detached edge node is excluded from all original-vertex tree queries.

    Subtree and path queries use original vertex IDs. ``subtree_value`` excludes
    the incoming parent edge, while ``path_cluster_value`` includes off-path DP branches.
    The callbacks and their algebraic requirements are the same as in
    ``RerootingLinkCutTree``. Vertex and edge payloads share ``ValueT``;
    use a tagged value when their meanings differ.

    The low-level ``set`` / ``get`` methods accept expanded node IDs from
    ``vs`` / ``es``. Use this wrapper's topology methods rather than modifying
    ``lct`` links directly, so edge-slot bookkeeping remains consistent.

    Attributes:
        n: Number of original vertices.
        vs: List of original vertex indices.
        es: List of edge-node indices corresponding to registered edges.
        lct: The constructed link-cut tree after `build()` is called.
        point_identity: Identity value for point aggregates.
        vertex_info: List of information values for original vertices.
        edge_info: List of information values for edges.
        graph: Initial-forest adjacency list, used only during construction.
        _add_vertex: Callback to attach a vertex value to a point aggregate.
        _add_edge: Callback to convert a path aggregate into an edge contribution.
        _rake: Callback to merge point aggregates.
        _point_inv: Callback for the inverse on point aggregates.
        _compress: Callback to merge path aggregates.

    Examples:
        The following example builds a path `0 - 1 - 2` whose original
        vertices have value `0` and whose edges have weights `5` and `7`.
        The aggregate is the sum of all values along the represented tree.

        >>> tree = RerootingLinkCutTreeWithEdges(
        ...     3,
        ...     point_identity=0,
        ...     add_vertex=lambda point, info: point + info,
        ...     add_edge=lambda path: path,
        ...     rake=lambda a, b: a + b,
        ...     point_inv=lambda x: -x,
        ...     compress=lambda a, b: a + b,
        ... )
        >>> tree.set_vertex(0, 0)
        >>> tree.set_vertex(1, 0)
        >>> tree.set_vertex(2, 0)
        >>> e0 = tree.add_edge(0, 1, 5)
        >>> e1 = tree.add_edge(1, 2, 7)
        >>> tree.build()
        >>> tree.tree_value(0)
        12
        >>> tree.set_edge(e0, 10)
        >>> tree.tree_value(2)
        17
        >>> tree.subtree_value(1, root=0)
        7
        >>> tree.cut_edge(e0)
        >>> tree.same(0, 2)
        False
        >>> tree.get_edge(e0)
        10
        >>> tree.link_edge(e0, 0, 2)
        >>> tree.tree_value(1)
        17

    Space Complexity:
        O(n + m), for n original vertices and m registered edge slots.
    """

    def __init__(
        self,
        n: int,
        point_identity: PointT,
        add_vertex: Callable[[PointT, ValueT], PathT],
        add_edge: Callable[[PathT], PointT],
        rake: Callable[[PointT, PointT], PointT],
        point_inv: Callable[[PointT], PointT],
        compress: Callable[[PathT, PathT], PathT],
    ) -> None:
        """
        Initialize the vertex and edge registration state.

        Args:
            n: Positive number of original vertices.
            point_identity: Identity value for point aggregates.
            add_vertex: Attaches a vertex value to an aggregate.
            add_edge: Converts a path aggregate into an edge contribution.
            rake: Commutative group operation on light-subtree aggregates.
            point_inv: Inverse under ``rake``.
            compress: Merges path aggregates.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is not positive.

        Time Complexity:
            O(n)
        """
        if n <= 0:
            raise ValueError('n must be positive')
        self.n = n
        self.point_identity = point_identity
        self._add_vertex = add_vertex
        self._add_edge = add_edge
        self._rake = rake
        self._point_inv = point_inv
        self._compress = compress
        self.vertex_info: list[ValueT | None] = [None] * n
        self.edge_info: list[ValueT] = []
        self.graph: list[list[tuple[int, int]]] = [[] for _ in range(n)]
        self._endpoints: list[tuple[int, int]] = []
        self._edge_active: list[bool] = []
        self.vs = list(range(n))
        self.es: list[int] = []
        self.lct: RerootingLinkCutTree[ValueT, PointT, PathT] | None = None

    def set_vertex(self, vertex: int, value: ValueT) -> None:
        """
        Initialize or overwrite the information of an original vertex.

        Args:
            vertex: Vertex index.
            value: Vertex payload. ``None`` is reserved for uninitialized values.

        Returns:
            None.

        Raises:
            IndexError: If the original vertex index is out of range.
            ValueError: If ``value`` is ``None``.

        Time Complexity:
            O(1) before build; O(log(n + m)) amortized afterwards.
        """
        self._validate_vertex(vertex)
        if value is None:
            raise ValueError('vertex value must not be None')
        if self.lct is None:
            self.vertex_info[vertex] = value
        else:
            self.set(vertex, value)

    def get_vertex(self, vertex: int) -> ValueT:
        """Return the current payload of an original vertex.

        Args:
            vertex: Original vertex index.

        Returns:
            Current vertex payload, before or after build.

        Raises:
            IndexError: If the vertex index is out of range.
            ValueError: If the vertex has not been initialized.

        Time Complexity:
            O(1).
        """
        self._validate_vertex(vertex)
        if self.lct is not None:
            return self.lct.get(vertex)
        info = self.vertex_info[vertex]
        if info is None:
            raise ValueError('vertex info has not been set')
        return info

    def set_edge(self, edge_id: int, value: ValueT) -> None:
        """Overwrite the payload of a registered edge, including a detached edge.

        Args:
            edge_id: Registered edge ID.
            value: New edge payload.

        Returns:
            None.

        Raises:
            IndexError: If the edge ID is out of range.

        Time Complexity:
            O(1) before build; O(log(n + m)) amortized afterwards.
        """
        self._validate_edge(edge_id)
        if self.lct is None:
            self.edge_info[edge_id] = value
        else:
            self.set(self.es[edge_id], value)

    def get_edge(self, edge_id: int) -> ValueT:
        """Return the current payload of a registered edge, including a detached edge.

        Args:
            edge_id: Registered edge ID.

        Returns:
            Current edge payload, before or after build.

        Raises:
            IndexError: If the edge ID is out of range.

        Time Complexity:
            O(1).
        """
        self._validate_edge(edge_id)
        if self.lct is not None:
            return self.lct.get(self.es[edge_id])
        return self.edge_info[edge_id]

    def add_edge(self, u: int, v: int, value: ValueT, edge_id: int = -1) -> int:
        """
        Register one initial undirected edge before build.

        Args:
            u: First vertex or endpoint index.
            v: Second vertex or endpoint index.
            value: Vertex or edge information value.
            edge_id: Next dense edge ID, or ``-1`` to assign it automatically.

        Returns:
            Assigned edge identifier.

        Raises:
            IndexError: If either original vertex index is out of range.
            ValueError: If already built, if the endpoints coincide, or if
                ``edge_id`` is not the next unused dense ID.

        Time Complexity:
            O(1) amortized.
        """
        if self.lct is not None:
            raise ValueError('register edge slots before build; reuse detached slots with link_edge')
        self._validate_vertex(u)
        self._validate_vertex(v)
        if u == v:
            raise ValueError('edge endpoints must differ')
        if edge_id == -1:
            edge_id = len(self.edge_info)
        if edge_id != len(self.edge_info):
            raise ValueError('edge id must be the next unused dense index')
        self.edge_info.append(value)
        self._endpoints.append((u, v))
        self._edge_active.append(True)
        self.graph[u].append((v, edge_id))
        self.graph[v].append((u, edge_id))
        return edge_id

    def build(self, root: int = 0) -> None:
        """
        Build the registered forest once, preserving its edge IDs.

        Args:
            root: Root of its component. Other components use their smallest
                original vertex as the root.

        Returns:
            None.

        Raises:
            IndexError: If ``root`` is out of range.
            ValueError: If already built, if a vertex payload is unset, or if
                the registered graph contains a cycle or parallel edges.

        Time Complexity:
            O((n + m) log(n + m)) amortized, assuming O(1) callbacks.
        """
        if self.lct is not None:
            raise ValueError('forest has already been built')
        self._validate_vertex(root)
        if any(info is None for info in self.vertex_info):
            raise ValueError('all vertex infos must be set before build')
        parent = [-2] * self.n
        parent_edge = [-1] * self.n
        order: list[int] = []
        for start in [root, *range(self.n)]:
            if parent[start] != -2:
                continue
            parent[start] = -1
            stack = [start]
            while stack:
                vertex = stack.pop()
                order.append(vertex)
                for child, edge_id in self.graph[vertex]:
                    if edge_id == parent_edge[vertex]:
                        continue
                    if parent[child] != -2:
                        raise ValueError('registered edges must form a forest')
                    parent[child] = vertex
                    parent_edge[child] = edge_id
                    stack.append(child)
        infos = [info for info in self.vertex_info if info is not None]
        infos.extend(self.edge_info)
        lct = RerootingLinkCutTree(
            infos,
            self.point_identity,
            self._add_vertex,
            self._add_edge,
            self._rake,
            self._point_inv,
            self._compress,
        )
        self.es = [self.n + edge_id for edge_id in range(len(self.edge_info))]
        for vertex in order:
            if parent[vertex] != -1:
                edge_vertex = self.es[parent_edge[vertex]]
                lct.link(edge_vertex, parent[vertex])
                lct.link(vertex, edge_vertex)
        self.lct = lct

    def set(self, vertex: int, value: ValueT) -> None:
        """
        Overwrite the value of a built vertex or edge node.

        Args:
            vertex: Expanded node ID: an original vertex or a node in ``es``.
            value: Vertex or edge information value.

        Returns:
            None.

        Raises:
            ValueError: If ``build`` has not been called.
            ValueError: If an original vertex is assigned ``None``.
            IndexError: If the expanded node ID is out of range.

        Time Complexity:
            O(log(n + m)) amortized.
        """
        lct = self._built_tree()
        if not 0 <= vertex < lct.n:
            raise IndexError('expanded node index out of range')
        if vertex < self.n and value is None:
            raise ValueError('vertex value must not be None')
        lct.set(vertex, value)
        if vertex < self.n:
            self.vertex_info[vertex] = value
        else:
            self.edge_info[vertex - self.n] = value

    def get(self, vertex: int) -> ValueT:
        """Return the payload of a built vertex or edge node.

        Args:
            vertex: Expanded node ID: an original vertex or a node in ``es``.

        Returns:
            Current node payload.

        Raises:
            ValueError: If ``build`` has not been called.
            IndexError: If the expanded node ID is out of range.

        Time Complexity:
            O(1).
        """
        lct = self._built_tree()
        if not 0 <= vertex < lct.n:
            raise IndexError('expanded node index out of range')
        return lct.get(vertex)

    def cut_edge(self, edge_id: int) -> None:
        """Detach both endpoints of an active edge, retaining its ID and payload.

        The components containing the stored endpoints ``u`` and ``v`` become
        rooted at ``u`` and ``v`` respectively. The edge node is isolated.

        Args:
            edge_id: Active edge ID to detach.

        Returns:
            None.

        Raises:
            IndexError: If the edge ID is out of range.
            ValueError: If not built or if the edge is already detached.

        Time Complexity:
            O(log(n + m)) amortized.
        """
        lct = self._built_tree()
        self._validate_edge(edge_id)
        if not self._edge_active[edge_id]:
            raise ValueError('edge is already detached')
        u, v = self._endpoints[edge_id]
        lct.reroot(u)
        lct.cut_parent(self.es[edge_id])
        lct.cut_parent(v)
        self._edge_active[edge_id] = False

    def link_edge(self, edge_id: int, child: int, parent: int) -> None:
        """Reconnect a detached edge slot between two different components.

        The component of ``child`` is rerooted at ``child`` and attached to ``parent`` via
        the edge node. The previous root of ``parent``'s component is preserved.

        Args:
            edge_id: Detached edge ID. Its payload is preserved.
            child: Original vertex on the child side.
            parent: Original vertex on the parent side.

        Returns:
            None.

        Raises:
            IndexError: If an edge or vertex index is out of range.
            ValueError: If not built, if the edge is already active, or if the
                endpoints are connected. Rejected links leave the forest intact.

        Time Complexity:
            O(log(n + m)) amortized.
        """
        lct = self._built_tree()
        self._validate_edge(edge_id)
        self._validate_vertex(child)
        self._validate_vertex(parent)
        if self._edge_active[edge_id]:
            raise ValueError('edge must be detached before linking')
        if lct.same(child, parent):
            raise ValueError('edge endpoints must belong to different components')
        edge_vertex = self.es[edge_id]
        lct.link(edge_vertex, parent)
        lct.link(child, edge_vertex)
        self._endpoints[edge_id] = (child, parent)
        self._edge_active[edge_id] = True

    def same(self, u: int, v: int) -> bool:
        """Return whether two original vertices belong to the same tree.

        Args:
            u: First original vertex.
            v: Second original vertex.

        Returns:
            Whether ``u`` and ``v`` are connected. Represented roots are preserved.

        Raises:
            ValueError: If not built.
            IndexError: If either vertex index is out of range.

        Time Complexity:
            O(log(n + m)) amortized.
        """
        lct = self._built_tree()
        self._validate_vertex(u)
        self._validate_vertex(v)
        return lct.same(u, v)

    def reroot(self, vertex: int) -> None:
        """Make an original vertex the root of its represented tree.

        This changes the root of the represented dynamic tree. Auxiliary
        splay-tree roots are managed internally.

        Args:
            vertex: New root, given as an original vertex index.

        Returns:
            None.

        Raises:
            ValueError: If not built.
            IndexError: If the vertex index is out of range.

        Time Complexity:
            O(log(n + m)) amortized.
        """
        lct = self._built_tree()
        self._validate_vertex(vertex)
        lct.reroot(vertex)

    def subtree_value(self, vertex: int, root: int | None = None) -> PathT:
        """Return the DP of a rooted subtree, excluding its incoming parent edge.

        Args:
            vertex: Original vertex at the root of the queried subtree.
            root: Optional original vertex in the same component to make the
                represented root. This root change persists. If omitted, the
                current represented root is used.

        Returns:
            DP value including the subtree's vertices and internal edges.

        Raises:
            IndexError: If a vertex index is out of range.
            ValueError: If not built or if ``root`` is in another component.

        Time Complexity:
            O(log(n + m)) amortized.
        """
        lct = self._built_tree()
        self._validate_vertex(vertex)
        if root is not None:
            self._validate_vertex(root)
            if not lct.same(vertex, root):
                raise ValueError('root must belong to the same component')
        return lct.subtree_value(vertex, root)

    def path_cluster_value(self, u: int, v: int) -> PathT:
        """Return the DP of an exposed path cluster, including attached branches.

        Args:
            u: Original start vertex and new represented root.
            v: Original end vertex in the same component.

        Returns:
            Path-cluster DP including vertex and edge payloads in off-path
            branches as well as the path. The represented root remains ``u``.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If not built or if the endpoints are disconnected.

        Time Complexity:
            O(log(n + m)) amortized.
        """
        lct = self._built_tree()
        self._validate_vertex(u)
        self._validate_vertex(v)
        if not lct.same(u, v):
            raise ValueError('path endpoints must be connected')
        return lct.path_cluster_value(u, v)

    def tree_value(self, vertex: int) -> PathT:
        """
        Return the whole-component DP when rooted at ``vertex``.

        The represented root becomes ``vertex`` and remains so after the query.

        Args:
            vertex: Expanded node ID. Normally an original vertex; a node in
                ``es`` may also be used to root the expanded tree at an edge.

        Returns:
            DP value of the component including both vertex and edge payloads.

        Raises:
            ValueError: If ``build`` has not been called.
            IndexError: If the expanded node ID is out of range.

        Time Complexity:
            O(log(n + m)) amortized.
        """
        lct = self._built_tree()
        if not 0 <= vertex < lct.n:
            raise IndexError('expanded node index out of range')
        return lct.tree_value(vertex)

    def _built_tree(self) -> RerootingLinkCutTree[ValueT, PointT, PathT]:
        if self.lct is None:
            raise ValueError('build must be called first')
        return self.lct

    def _validate_vertex(self, vertex: int) -> None:
        if not 0 <= vertex < self.n:
            raise IndexError('original vertex index out of range')

    def _validate_edge(self, edge_id: int) -> None:
        if not 0 <= edge_id < len(self.edge_info):
            raise IndexError('edge index out of range')
