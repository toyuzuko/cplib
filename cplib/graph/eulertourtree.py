#!/usr/bin/env python3

from __future__ import annotations

from typing import Generic
from collections.abc import Callable, Iterator, Sequence
from cplib.tools.type import ValueT


class EulerTourTree(Generic[ValueT]):
    """
    Euler Tour Tree for dynamic forests with component aggregates.

    The structure represents each tree as a cyclic Euler tour stored in an
    implicit treap. Every vertex owns one dedicated loop node that appears
    exactly once in the tour, while each undirected edge contributes two
    directed edge nodes. Component aggregates are therefore taken over the
    vertex loop nodes only.

    This implementation is intended as the base building block for online
    dynamic connectivity. It supports:

    - ``link(child, parent)``: attach one component under a vertex of another
    - ``cut(u, v)``: remove an existing tree edge
    - ``reroot(v)``: rotate the Euler tour so ``v`` becomes the tree root
    - ``same(u, v)``: test connectivity
    - ``set(v, x)`` / ``get(v)``: update one vertex payload
    - ``component_aggregate(v)``: aggregate over the connected component of ``v``

    Because the Euler tour order depends on the current root and on the
    sequence of updates, ``op`` should be treated as a commutative monoid when
    used for component aggregates.

    Deleted edge nodes are reused. Allocated storage depends on the largest
    forest held at once, rather than the number of link/cut operations.

    Attributes:
        n: Number of vertices.
        e: Identity element of ``op``.
        op: Associative operation for component aggregation.
        root_node: Maps each vertex to its loop node.
        edge_node: Maps each undirected edge to its pair of directed edge nodes.
        val: Payload values of all nodes.
        acc: Component aggregates of all nodes.
        mark_val: Auxiliary marker values of all nodes.
        mark_acc: Component aggregates of marker values for all nodes.
        pri: Treap priorities of all nodes.
        ptr: Child pointers of all nodes, where ptr[node << 1] and ptr[node << 1 | 1] are the left and right children of node, respectively.
        par: Parent pointers of all nodes.
        size: Sizes of all subtrees.
        vertex_count: Number of vertex loop nodes in all subtrees.
        is_vertex: Indicator of whether each node is a vertex loop node.
        vertex_id: Maps each vertex loop node to its vertex ID, or ``-1`` for edge nodes.

    Examples:
        >>> from operator import add
        >>> ett = EulerTourTree(3, 0, add)
        >>> ett.build([1, 2, 3])
        >>> ett.link(0, 1)
        >>> ett.link(1, 2)
        >>> ett.component_aggregate(0)
        6
        >>> ett.cut(1, 2)
        >>> ett.same(0, 2)
        False

    Space Complexity:
        O(n)
    """

    __slots__ = ('n', 'e', 'op', 'root_node', 'edge_node', 'val', 'acc', 'mark_val', 'mark_acc', 'pri', 'ptr', 'par', 'size', 'vertex_count', 'is_vertex', 'vertex_id', '_rand', '_free')

    def __init__(self, n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT]) -> None:
        """
        Initialize a forest of ``n`` isolated vertices.

        Args:
            n: Number of vertices.
            e: Identity element of ``op``.
            op: Associative operation for component aggregation. This should ideally be a commutative monoid operation, as the Euler tour order is not fixed.

        Returns:
            None.

        Time Complexity:
            O(n)
        """
        self.n = n
        self.e = e
        self.op = op
        self.root_node = [0] * n
        self.edge_node: dict[tuple[int, int], tuple[int, int]] = {}
        self.val: list[ValueT] = [e]
        self.acc: list[ValueT] = [e]
        self.mark_val = [0]
        self.mark_acc = [0]
        self.pri: list[int] = [1 << 32]
        self.ptr: list[int] = [0, 0]
        self.par: list[int] = [0]
        self.size: list[int] = [0]
        self.vertex_count: list[int] = [0]
        self.is_vertex: list[int] = [0]
        self.vertex_id: list[int] = [-1]
        self._rand = self._xor64()
        self._free: list[int] = []

        for v in range(n):
            node = self._new_node(e, 1)
            self.root_node[v] = node
            self.vertex_id[node] = v

    def _xor64(self) -> Iterator[int]:
        x = 88172645463325252
        while True:
            x ^= (x << 7) & 0xFFFFFFFF
            x ^= x >> 9
            yield x & 0xFFFFFFFF

    def _new_node(self, value: ValueT, is_vertex: int) -> int:
        if self._free:
            idx = self._free.pop()
            self.val[idx] = value
            self.acc[idx] = value if is_vertex else self.e
            self.mark_val[idx] = self.mark_acc[idx] = 0
            self.pri[idx] = next(self._rand)
            self.ptr[idx << 1] = self.ptr[idx << 1 | 1] = 0
            self.par[idx] = 0
            self.size[idx] = 1
            self.vertex_count[idx] = self.is_vertex[idx] = is_vertex
            self.vertex_id[idx] = -1
            return idx
        idx = len(self.val)
        self.val.append(value)
        self.acc.append(value if is_vertex else self.e)
        self.mark_val.append(0)
        self.mark_acc.append(0)
        self.pri.append(next(self._rand))
        self.ptr.extend([0, 0])
        self.par.append(0)
        self.size.append(1)
        self.vertex_count.append(is_vertex)
        self.is_vertex.append(is_vertex)
        self.vertex_id.append(-1)
        return idx

    def _left(self, node: int) -> int:
        return self.ptr[node << 1]

    def _right(self, node: int) -> int:
        return self.ptr[node << 1 | 1]

    def _set_left(self, node: int, child: int) -> None:
        self.ptr[node << 1] = child
        if child:
            self.par[child] = node

    def _set_right(self, node: int, child: int) -> None:
        self.ptr[node << 1 | 1] = child
        if child:
            self.par[child] = node

    def _update(self, node: int) -> None:
        left = self._left(node)
        right = self._right(node)
        self.size[node] = self.size[left] + self.size[right] + 1
        self.vertex_count[node] = self.vertex_count[left] + self.vertex_count[right] + self.is_vertex[node]
        value = self.val[node] if self.is_vertex[node] else self.e
        self.acc[node] = self.op(self.op(self.acc[left], value), self.acc[right])
        self.mark_acc[node] = self.mark_acc[left] + self.mark_acc[right] + self.mark_val[node]

    def _root(self, node: int) -> int:
        while self.par[node]:
            node = self.par[node]
        return node

    def _index(self, node: int) -> int:
        index = self.size[self._left(node)]
        while self.par[node]:
            parent = self.par[node]
            if self._right(parent) == node:
                index += self.size[self._left(parent)] + 1
            node = parent
        return index

    def _merge(self, left: int, right: int) -> int:
        if left == 0 or right == 0:
            root = left or right
            if root:
                self.par[root] = 0
            return root
        if self.pri[left] < self.pri[right]:
            new_right = self._merge(self._right(left), right)
            self._set_right(left, new_right)
            self._update(left)
            self.par[left] = 0
            return left
        new_left = self._merge(left, self._left(right))
        self._set_left(right, new_left)
        self._update(right)
        self.par[right] = 0
        return right

    def _split(self, root: int, k: int) -> tuple[int, int]:
        if root == 0:
            return (0, 0)
        left_size = self.size[self._left(root)]
        if k <= left_size:
            left, new_left_child = self._split(self._left(root), k)
            self._set_left(root, new_left_child)
            self._update(root)
            self.par[root] = 0
            if left:
                self.par[left] = 0
            return (left, root)
        new_right_child, right = self._split(self._right(root), k - left_size - 1)
        self._set_right(root, new_right_child)
        self._update(root)
        self.par[root] = 0
        if right:
            self.par[right] = 0
        return (root, right)

    def build(self, values: Sequence[ValueT]) -> None:
        """
        Initialize vertex values before linking any edges.

        Call this only during initialization, before the first ``link``.
        It does not rebuild aggregates of an existing forest. Use ``set``
        to update vertex values after linking.

        Args:
            values: Initial values for vertices ``0`` through ``n - 1``.

        Returns:
            None.

        Time Complexity:
            O(n).

        Raises:
            ValueError: If ``values`` does not have length ``n``.
        """
        if len(values) != self.n:
            raise ValueError('values length must match n')
        for v, value in enumerate(values):
            node = self.root_node[v]
            self.val[node] = value
            self.acc[node] = value

    def same(self, u: int, v: int) -> bool:
        """
        Return whether ``u`` and ``v`` are in the same tree.

        Args:
            u: First vertex.
            v: Second vertex.

        Returns:
            ``True`` if the two vertices are connected, otherwise ``False``.

        Time Complexity:
            O(log n) expected.
        """
        return self._root(self.root_node[u]) == self._root(self.root_node[v])

    def reroot(self, v: int) -> None:
        """
        Rotate the Euler tour so ``v`` becomes the tree root.

        Args:
            v: New root of the represented tree.

        Returns:
            None.

        Time Complexity:
            O(log n) expected.
        """
        node = self.root_node[v]
        root = self._root(node)
        idx = self._index(node)
        left, right = self._split(root, idx)
        root = self._merge(right, left)
        if root:
            self.par[root] = 0

    def link(self, child: int, parent: int) -> None:
        """
        Reroot the child's tree and attach it under ``parent``.

        The start of the parent's Euler tour is preserved. Rejected links
        preserve the forest and its Euler tours.

        Args:
            child: Endpoint to make the root of its component before linking.
            parent: Endpoint in a different component to attach under.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the endpoints already belong to the same tree.

        Time Complexity:
            O(log n) expected.
        """
        if not (0 <= child < self.n and 0 <= parent < self.n):
            raise IndexError('vertex index out of range')
        if self.same(child, parent):
            raise ValueError('link requires different components')
        self.reroot(child)
        child_root = self._root(self.root_node[child])
        parent_node = self.root_node[parent]
        parent_root = self._root(parent_node)
        left, right = self._split(parent_root, self._index(parent_node) + 1)
        down = self._new_node(self.e, 0)
        up = self._new_node(self.e, 0)
        key = (child, parent) if child < parent else (parent, child)
        self.edge_node[key] = (up, down) if child < parent else (down, up)
        merged = self._merge(self._merge(self._merge(self._merge(left, down), child_root), up), right)
        self.par[merged] = 0

    def cut(self, u: int, v: int) -> None:
        """
        Remove the tree edge ``(u, v)``.

        Args:
            u: First endpoint.
            v: Second endpoint.

        Returns:
            None.

        Raises:
            IndexError: If either vertex index is out of range.
            ValueError: If the edge does not exist as a tree edge.

        Time Complexity:
            O(log n) expected.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        key = (u, v) if u < v else (v, u)
        if key not in self.edge_node:
            raise ValueError('edge does not exist')
        a, b = self.edge_node.pop(key)
        root = self._root(a)
        pos_a = self._index(a)
        pos_b = self._index(b)
        if pos_a > pos_b:
            a, b = b, a
            pos_a, pos_b = pos_b, pos_a
        left, rest = self._split(root, pos_a)
        _, rest = self._split(rest, 1)
        middle, rest = self._split(rest, pos_b - pos_a - 1)
        _, right = self._split(rest, 1)
        first = middle
        second = self._merge(right, left)
        if first:
            self.par[first] = 0
        if second:
            self.par[second] = 0
        self._free.extend((a, b))

    def set(self, v: int, value: ValueT) -> None:
        """
        Overwrite the payload of vertex ``v``.

        Args:
            v: Target vertex.
            value: New payload value.

        Returns:
            None.

        Time Complexity:
            O(log n) expected.
        """
        node = self.root_node[v]
        self.val[node] = value
        while node:
            self._update(node)
            node = self.par[node]

    def get(self, v: int) -> ValueT:
        """
        Return the payload stored at vertex ``v``.

        Args:
            v: Target vertex.

        Returns:
            The current payload of ``v``.

        Time Complexity:
            O(1).
        """
        return self.val[self.root_node[v]]

    def set_mark(self, v: int, mark: int) -> None:
        """
        Set the auxiliary marker value of vertex ``v``.

        Args:
            v: Target vertex.
            mark: New non-negative marker value.

        Returns:
            None.

        Time Complexity:
            O(log n) expected.
        """
        node = self.root_node[v]
        self.mark_val[node] = mark
        while node:
            self._update(node)
            node = self.par[node]

    def component_has_marked(self, v: int) -> bool:
        """
        Return whether the component containing ``v`` has a marked vertex.

        Args:
            v: Any vertex in the target component.

        Returns:
            ``True`` if some vertex in the component has a positive marker value, otherwise ``False``.

        Time Complexity:
            O(log n) expected.
        """
        return self.mark_acc[self._root(self.root_node[v])] > 0

    def find_marked(self, v: int) -> int:
        """
        Return one marked vertex in the component containing ``v``.

        Args:
            v: Any vertex in the target component.

        Returns:
            A vertex whose marker value is positive, or ``-1`` if no such vertex exists.

        Time Complexity:
            O(log n) expected.

        """
        node = self._root(self.root_node[v])
        if self.mark_acc[node] == 0:
            return -1
        while True:
            left = self._left(node)
            if self.mark_acc[left] > 0:
                node = left
                continue
            if self.is_vertex[node] and self.mark_val[node] > 0:
                return self.vertex_id[node]
            node = self._right(node)

    def component_aggregate(self, v: int) -> ValueT:
        """
        Return the aggregate of the connected component containing ``v``.

        Args:
            v: Any vertex in the target component.

        Returns:
            Aggregate of all vertex payloads in the connected component.

        Time Complexity:
            O(log n) expected.
        """
        return self.acc[self._root(self.root_node[v])]

    def component_size(self, v: int) -> int:
        """
        Return the number of vertices in the component containing ``v``.

        Args:
            v: Any vertex in the target component.

        Returns:
            Number of vertices in the connected component.

        Time Complexity:
            O(log n) expected.
        """
        return self.vertex_count[self._root(self.root_node[v])]

    def component_vertices(self, v: int) -> list[int]:
        """
        Return the vertices in the component containing ``v``.

        Args:
            v: Any vertex in the target component.

        Returns:
            A list of vertices in Euler-tour order, each appearing exactly once.

        Time Complexity:
            O(k + log n) expected, where ``k`` is the component size.
        """
        root = self._root(self.root_node[v])
        result: list[int] = []
        stack: list[int] = []
        node = root
        while stack or node:
            while node:
                stack.append(node)
                node = self._left(node)
            node = stack.pop()
            if self.is_vertex[node]:
                result.append(self.vertex_id[node])
            node = self._right(node)
        return result
