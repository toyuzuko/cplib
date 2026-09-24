#!/usr/bin/env python3

"""Tree query data structures and builders.

This module groups reusable helpers for static rooted-tree queries, including
subtree sack traversal, virtual-tree construction, path folds, and
distance-contour aggregation.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Generic, NamedTuple, cast

from cplib.datastructure.fenwicktree import GroupFenwickTree, GroupRangeAddPointGet
from cplib.datastructure.segtree import SegmentTree
from cplib.graph.base import Node, Weight
from cplib.graph.core import Tree
from cplib.graph.treedecomp import CentroidDecomposition, HeavyLightDecomposition
from cplib.tools.type import ValueT


class DSUOnTree(Generic[ValueT]):
    """
    Reusable executor for subtree queries on a rooted tree.

    DSU on Tree, also called the sack technique, answers every subtree query by
    maintaining one mutable active state. The caller supplies three callbacks:
    ``add(v)`` inserts one vertex into that state, ``remove(v)`` deletes one
    vertex from it, and ``answer(v)`` reads the answer for vertex ``v``.

    During ``run()``, this class orders the callback calls so that when
    ``answer(v)`` is called, the active state contains exactly the vertices in
    the subtree of ``v``. This is useful for subtree statistics such as:

    - number of distinct colors in each subtree
    - maximum frequency in each subtree
    - sums, counters, or other mutable aggregates over subtree vertices

    Attributes:
        euler: Euler-tour order of vertices.
        tin: Entry time of each vertex in ``euler``.
        tout: Exit time of each vertex in ``euler`` as a half-open interval end.
        heavy: Heavy child of each vertex, or ``-1`` for leaves.

    Complexity Notation:
        n: Number of vertices in the tree.

    Space Complexity:
        - ``O(n)``

    Examples:
        Count distinct colors in every subtree.

        >>> tree = Tree(5)
        >>> tree.add_edge(Node(0), Node(1))
        >>> tree.add_edge(Node(0), Node(2))
        >>> tree.add_edge(Node(1), Node(3))
        >>> tree.add_edge(Node(1), Node(4))
        >>> tree.build(Node(0))
        >>> colors = [1, 2, 1, 2, 3]
        >>> freq: dict[int, int] = {}
        >>> distinct = [0]
        >>> solver = DSUOnTree[int](tree)
        >>> def add(v: Node) -> None:
        ...     color = colors[v]
        ...     freq[color] = freq.get(color, 0) + 1
        ...     if freq[color] == 1:
        ...         distinct[0] += 1
        >>> def remove(v: Node) -> None:
        ...     color = colors[v]
        ...     freq[color] -= 1
        ...     if freq[color] == 0:
        ...         distinct[0] -= 1
        ...         del freq[color]
        >>> def answer(_: Node) -> int:
        ...     return distinct[0]
        >>> solver.run(add, remove, answer)
        [3, 2, 1, 1, 1]
    """

    def __init__(self, tree: Tree) -> None:
        """Preprocess a rooted tree for DSU-on-tree traversal.

        Args:
            tree: Rooted tree. ``tree.build()`` must already have been called.

        Returns:
            ``None``.

        Raises:
            ValueError: If the tree has not been built.

        Time Complexity:
            - ``O(n)``
        """
        if tree.root == -1:
            raise ValueError("tree must be built before creating DSUOnTree")
        self.tree = tree
        self.n = tree.n
        self.root = tree.root
        self.euler: list[Node] = []
        self.tin = [0] * self.n
        self.tout = [0] * self.n
        self.heavy = [Node(-1)] * self.n

        for v in range(self.n):
            best_size = -1
            for to, _ in tree.tree[v]:
                if to == tree.par_v[v]:
                    continue
                if tree.size[to] > best_size:
                    best_size = tree.size[to]
                    self.heavy[v] = to

        stack: list[tuple[Node, bool]] = [(self.root, False)]
        while stack:
            v, exiting = stack.pop()
            if not exiting:
                self.tin[v] = len(self.euler)
                self.euler.append(v)
                stack.append((v, True))
                children = [to for to, _ in tree.tree[v] if to != tree.par_v[v]]
                for to in reversed(children):
                    stack.append((to, False))
            else:
                self.tout[v] = len(self.euler)

    def subtree_range(self, v: Node) -> tuple[int, int]:
        """
        Return the Euler-tour interval of a subtree.

        Args:
            v: Root of the subtree.

        Returns:
            Pair ``(l, r)`` such that ``euler[l:r]`` is exactly the subtree.

        Raises:
            IndexError: If ``v`` is outside ``[0, n)``.

        Time Complexity:
            - ``O(1)``
        """
        if not 0 <= v < self.n:
            raise IndexError("vertex index out of range")
        return self.tin[v], self.tout[v]

    def run(self, add: Callable[[Node], None], remove: Callable[[Node], None], answer: Callable[[Node], ValueT]) -> list[ValueT]:
        """
        Execute the DSU-on-tree traversal and collect results.

        Args:
            add: Add one vertex to the active state.
            remove: Remove one vertex from the active state.
            answer: Return the result for one vertex after its full subtree has
                been added. At that moment, the active state contains exactly
                the vertices in the subtree of the queried vertex.

        Returns:
            List ``res`` such that ``res[v] = answer(v)``.

        Time Complexity:
            - ``O(n log n)`` total callback invocations, plus the cost of those callbacks

        Examples:
            >>> tree = Tree(2)
            >>> tree.add_edge(Node(0), Node(1))
            >>> tree.build(Node(0))
            >>> solver = DSUOnTree[int](tree)
            >>> solver.run(lambda v: None, lambda v: None, lambda v: int(v))
            [0, 1]
        """
        result: list[ValueT | None] = [None] * self.n

        def add_subtree(v: Node) -> None:
            left, right = self.subtree_range(v)
            for i in range(left, right):
                add(self.euler[i])

        def remove_subtree(v: Node) -> None:
            left, right = self.subtree_range(v)
            for i in range(left, right):
                remove(self.euler[i])

        stack: list[tuple[Node, bool, int]] = [(self.root, True, 0)]
        while stack:
            v, keep, state = stack.pop()
            heavy_child = self.heavy[v]
            if state == 0:
                stack.append((v, keep, 1))
                children = [
                    to for to, _ in self.tree.tree[v]
                    if to != self.tree.par_v[v] and to != heavy_child
                ]
                for to in reversed(children):
                    stack.append((to, False, 0))
            elif state == 1:
                stack.append((v, keep, 2))
                if heavy_child != -1:
                    stack.append((heavy_child, True, 0))
            elif state == 2:
                for to, _ in self.tree.tree[v]:
                    if to == self.tree.par_v[v] or to == heavy_child:
                        continue
                    add_subtree(to)
                add(v)
                result[v] = answer(v)
                if not keep:
                    remove_subtree(v)

        return [cast(ValueT, value) for value in result]


class VirtualTreeResult(NamedTuple):
    """
    Result of one virtual-tree construction.

    Attributes:
        tree: Compressed rooted tree on virtual-node indices.
        original: ``original[i]`` is the original vertex represented by
            virtual node ``i``.
        virtual_id: ``virtual_id[v]`` is the virtual-node index of original
            vertex ``v``, or ``-1`` if ``v`` is not present in the result.

    The returned tree stores original-tree path lengths as edge weights.

    Space Complexity:
        - ``O(n + k)``, where ``n`` counts original vertices and ``k`` counts virtual nodes.
          ``virtual_id`` always has length ``n``.
    """

    tree: Tree
    original: list[Node]
    virtual_id: list[int]


class VirtualTreeBuilder:
    """
    Build virtual trees from repeated subset queries on one rooted tree.

    The builder preprocesses a rooted tree once and then supports:

    - lowest common ancestor queries
    - DFS-order sorting via ``tin`` / ``tout``
    - compressed tree construction with LCAs auto-inserted

    Attributes:
        tree: Original rooted tree.
        root: Root of the original tree.
        hld: Heavy-light decomposition used for LCA queries.
        depth: Depth of each original vertex.
        order: DFS order of original vertices.
        tin: Entry time of each vertex in ``order``.
        tout: Exit time of each vertex as a half-open interval end.

    Space Complexity:
        - ``O(n)`` n is the number of vertices in the original tree.

    Examples:
        >>> tree = Tree(10)
        >>> tree.add_edge(Node(0), Node(1))
        >>> tree.add_edge(Node(0), Node(2))
        >>> tree.add_edge(Node(1), Node(3))
        >>> tree.add_edge(Node(1), Node(4))
        >>> tree.add_edge(Node(3), Node(5))
        >>> tree.add_edge(Node(3), Node(6))
        >>> tree.add_edge(Node(2), Node(7))
        >>> tree.add_edge(Node(7), Node(8))
        >>> tree.add_edge(Node(7), Node(9))
        >>> tree.build(Node(0))
        >>> builder = VirtualTreeBuilder(tree)
        >>> result = builder.build([Node(5), Node(6), Node(8), Node(9)])
        >>> result.original
        [0, 3, 5, 6, 7, 8, 9]
    """

    def __init__(self, tree: Tree) -> None:
        """Preprocess one rooted tree for future virtual-tree queries.

        Args:
            tree: A rooted tree created by ``Tree.build()``.

        Returns:
            None.

        Raises:
            ValueError: If the tree has not been built yet.

        Time Complexity:
            - ``O(n)``
        """
        if tree.root == -1:
            raise ValueError('tree must be built before constructing a virtual tree')

        self.tree = tree
        self.root = tree.root
        self.hld = HeavyLightDecomposition(tree)
        self.depth = list(tree.dep)
        self.order: list[Node] = []
        self.tin = [0] * tree.n
        self.tout = [0] * tree.n
        self._build_dfs_order()

    def lca(self, u: int, v: int) -> int:
        """
        Return the lowest common ancestor of two vertices.

        Args:
            u: First vertex.
            v: Second vertex.

        Returns:
            Lowest common ancestor of ``u`` and ``v``.

        Time Complexity:
            - ``O(log n)``
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        return int(self.hld.lca(Node(u), Node(v)))

    def build(self, vertices: Sequence[int]) -> VirtualTreeResult:
        """
        Build the virtual tree induced by the given vertices.

        The input vertices are deduplicated, sorted in DFS order, and augmented
        with the LCAs needed to connect them. The returned tree is rooted at the
        highest resulting vertex in the original tree.

        Args:
            vertices: Vertices to keep in the compressed tree.

        Returns:
            ``VirtualTreeResult`` containing the compressed tree and the maps
            between original-vertex ids and virtual-node ids. An empty input
            returns an unbuilt ``Tree(0)``, an empty ``original`` list, and a
            length-``n`` ``virtual_id`` list filled with ``-1``.

        Time Complexity:
            - ``O(n + k log k + k log n)``, where ``n`` is the original vertex
              count and ``k`` is the input length. Building the dense
              ``virtual_id`` map takes ``O(n)`` even for an empty input.

        Space Complexity:
            - ``O(n + k)`` including the returned mapping arrays.
        """
        if not vertices:
            return VirtualTreeResult(Tree(0), [], [-1] * self.tree.n)

        nodes = self._normalize_vertices(vertices)
        nodes.sort(key=self.tin.__getitem__)
        nodes = self._add_lcas(nodes)

        index = {vertex: i for i, vertex in enumerate(nodes)}
        compressed = Tree(len(nodes))
        stack: list[int] = []

        for vertex in nodes:
            while stack and not self._is_ancestor(stack[-1], vertex):
                stack.pop()
            if stack:
                parent = stack[-1]
                compressed.add_edge(
                    Node(index[parent]),
                    Node(index[vertex]),
                    Weight(self.tree.cost[vertex] - self.tree.cost[parent]),
                )
            stack.append(vertex)

        compressed.build(Node(0))
        virtual_id = [-1] * self.tree.n
        for i, vertex in enumerate(nodes):
            virtual_id[vertex] = i
        return VirtualTreeResult(
            tree=compressed,
            original=[Node(vertex) for vertex in nodes],
            virtual_id=virtual_id,
        )

    def _normalize_vertices(self, vertices: Sequence[int]) -> list[int]:
        seen: set[int] = set()
        result: list[int] = []
        for vertex in vertices:
            self._validate_vertex(vertex)
            if vertex in seen:
                continue
            seen.add(vertex)
            result.append(vertex)
        return result

    def _add_lcas(self, nodes: list[int]) -> list[int]:
        if len(nodes) <= 1:
            return nodes[:]
        augmented = nodes[:]
        for i in range(len(nodes) - 1):
            augmented.append(self.lca(nodes[i], nodes[i + 1]))
        return sorted(set(augmented), key=self.tin.__getitem__)

    def _build_dfs_order(self) -> None:
        timer = 0
        stack: list[tuple[int, int]] = [(int(self.root), 0)]
        while stack:
            vertex, state = stack.pop()
            if state == 0:
                self.tin[vertex] = timer
                self.order.append(Node(vertex))
                timer += 1
                stack.append((vertex, 1))
                for to, _ in reversed(self.tree.tree[vertex]):
                    if to == self.tree.par_v[vertex]:
                        continue
                    stack.append((int(to), 0))
            else:
                self.tout[vertex] = timer

    def _is_ancestor(self, u: int, v: int) -> bool:
        return self.tin[u] <= self.tin[v] < self.tout[u]

    def _validate_vertex(self, vertex: int) -> None:
        if not 0 <= vertex < self.tree.n:
            raise IndexError('vertex index out of range')


class TreePathQuery(Generic[ValueT]):
    """
    Support path and subtree folds on a static rooted tree.

    Values can be stored either on vertices or on edges. Internally the
    structure places them on the heavy-light order and keeps both forward and
    reverse products in a segment tree so path queries can respect direction.

    Space Complexity:
        - ``O(n)``

    Complexity Notation:
        ``n`` is the number of vertices.

    Args:
        tree: Tree object used by the data structure or algorithm.
        values: Initial values.
        op: Associative binary operation.
        e: Identity element for the operation.
        edge_query: If True, values are indexed by edges; otherwise by vertices.

    Raises:
        ValueError: If tree is not built or values has the wrong length.
    """

    __slots__ = (
        'tree',
        'op',
        'e',
        'edge_query',
        '_hld',
        '_segment_tree',
        '_position',
        '_size',
    )

    def __init__(self, tree: Tree, values: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT], e: ValueT, edge_query: bool = False) -> None:
        """Initialize a static path-query structure.

        Args:
            tree: Built rooted tree.
            values: Initial values. Its length must be ``tree.n`` for
                vertex queries and ``tree.m`` for edge queries.
            op: Associative fold operation on stored values.
            e: Identity element of ``op``.
            edge_query: If ``False``, store values on vertices. If ``True``,
                store values on edges and interpret path/subtree queries as
                operating on edges instead.

        Returns:
            None.

        Raises:
            ValueError: If ``tree`` is not built or ``values`` has invalid length.

        Time Complexity:
            O(n)
        """
        if tree.root == -1:
            raise ValueError('tree must be built before constructing TreePathQuery')

        self.tree = tree
        self.op = op
        self.e = e
        self.edge_query = edge_query
        self._hld = HeavyLightDecomposition(tree)
        self._size = tree.m if edge_query else tree.n

        if len(values) != self._size:
            kind = 'edges' if edge_query else 'vertices'
            raise ValueError(f'values must contain exactly {self._size} {kind}')

        base = [(e, e) for _ in range(tree.n)]
        if edge_query:
            self._position = [-1] * tree.m
            root = int(tree.root)
            for vertex in range(tree.n):
                if vertex == root:
                    continue
                edge_index = int(tree.par_e[vertex])
                position = self._hld.id[vertex]
                value = values[edge_index]
                base[position] = (value, value)
                self._position[edge_index] = position
        else:
            self._position = [0] * tree.n
            for vertex, value in enumerate(values):
                position = self._hld.id[vertex]
                base[position] = (value, value)
                self._position[vertex] = position

        self._segment_tree = SegmentTree[tuple[ValueT, ValueT]](tree.n, self._merge_pair, (e, e))
        self._segment_tree.build(base)

    def set(self, index: int, value: ValueT) -> None:
        """
        Overwrite one stored vertex or edge value.

        Args:
            index: Vertex index or edge index, depending on ``edge_query``.
            value: New stored value.

        Returns:
            None.

        Time Complexity:
            O(log n)
        """
        self._validate_index(index)
        self._segment_tree.set(self._position[index], (value, value))

    def get(self, index: int) -> ValueT:
        """
        Return one stored vertex or edge value.

        Args:
            index: Vertex index or edge index, depending on ``edge_query``.

        Returns:
            ValueT: Stored value at ``index``.

        Time Complexity:
            O(log n)
        """
        self._validate_index(index)
        return self._segment_tree.get(self._position[index])[0]

    def path_prod(self, u: int, v: int) -> ValueT:
        """
        Fold values on the simple path between ``u`` and ``v``.

        Args:
            u: One endpoint of the path.
            v: The other endpoint of the path.

        Returns:
            ValueT: Fold of the path in order from ``u`` to ``v``.

        Time Complexity:
            O(log^2 n)
        """
        self._validate_vertex(u)
        self._validate_vertex(v)

        left = self.e
        right = self.e
        left_vertex = u
        right_vertex = v

        while self._hld.top[left_vertex] != self._hld.top[right_vertex]:
            left_top = int(self._hld.top[left_vertex])
            right_top = int(self._hld.top[right_vertex])
            if self._hld.id[left_top] > self._hld.id[right_top]:
                segment = self._range_prod(
                    self._hld.id[left_top],
                    self._hld.id[left_vertex] + 1,
                    reverse=True,
                )
                left = self.op(left, segment)
                left_vertex = int(self.tree.par_v[left_top])
            else:
                segment = self._range_prod(
                    self._hld.id[right_top],
                    self._hld.id[right_vertex] + 1,
                    reverse=False,
                )
                right = self.op(segment, right)
                right_vertex = int(self.tree.par_v[right_top])

        left_id = self._hld.id[left_vertex]
        right_id = self._hld.id[right_vertex]
        offset = 1 if self.edge_query else 0

        if left_id > right_id:
            segment = self._range_prod(right_id + offset, left_id + 1, reverse=True)
            left = self.op(left, segment)
        else:
            segment = self._range_prod(left_id + offset, right_id + 1, reverse=False)
            right = self.op(segment, right)
        return self.op(left, right)

    def subtree_prod(self, vertex: int) -> ValueT:
        """
        Fold values in the rooted subtree of ``vertex`` in heavy-light order.

        The operation may be non-commutative. The fold follows increasing HLD
        positions, rather than vertex indices or adjacency-list order.

        Args:
            vertex: Root of the queried subtree.

        Returns:
            ValueT: Fold over the subtree of ``vertex``. In edge-query mode, the edge
            from the parent of ``vertex`` is excluded.

        Time Complexity:
            O(log n)
        """
        self._validate_vertex(vertex)
        left, right = self._hld.subtree_range(Node(vertex))
        start = left + (1 if self.edge_query else 0)
        return self._range_prod(start, right, reverse=False)

    def _merge_pair(self, left: tuple[ValueT, ValueT], right: tuple[ValueT, ValueT]) -> tuple[ValueT, ValueT]:
        return (
            self.op(left[0], right[0]),
            self.op(right[1], left[1]),
        )

    def _range_prod(self, left: int, right: int, reverse: bool) -> ValueT:
        result = self._segment_tree.prod(left, right)
        return result[1] if reverse else result[0]

    def _validate_vertex(self, vertex: int) -> None:
        if not 0 <= vertex < self.tree.n:
            raise IndexError('vertex index out of range')

    def _validate_index(self, index: int) -> None:
        if not 0 <= index < self._size:
            raise IndexError('stored index out of range')


class _DepthBuckets(Generic[ValueT]):
    def __init__(
        self,
        pairs: list[tuple[int, int]],
        values: Sequence[ValueT],
        op: Callable[[ValueT, ValueT], ValueT],
        inv: Callable[[ValueT], ValueT],
        e: ValueT,
    ) -> None:
        self.starts: list[int]
        size = len(pairs)
        if size == 0:
            self.starts = [0]
            self.bit = GroupFenwickTree(0, op, inv, e)
            return
        max_depth = pairs[-1][0]
        self.starts = [0] * (max_depth + 2)
        arr = [e] * size
        position: dict[int, int] = {}
        i = 0
        for depth in range(max_depth + 1):
            self.starts[depth] = i
            while i < size and pairs[i][0] == depth:
                _, vertex = pairs[i]
                arr[i] = values[vertex]
                position[vertex] = i
                i += 1
        self.starts[max_depth + 1] = size
        self.position = position
        self.bit = GroupFenwickTree(size, op, inv, e)
        self.bit.build(arr)

    def add_vertex(self, vertex: int, value: ValueT) -> None:
        """
        add_vertex API.

        Args:
            vertex: Vertex index.
            value: Stored value or update value.

        Time Complexity:
            O(log n)
        Space Complexity:
            O(1) auxiliary space
        """
        self.bit.add(self.position[vertex], value)

    def prod_by_depth(self, l: int, r: int) -> ValueT:
        """
        prod_by_depth API.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.

        Time Complexity:
            O(log n)
        Space Complexity:
            O(1) auxiliary space
        """
        if r <= 0:
            return self.bit.e
        l = max(l, 0)
        upper = len(self.starts) - 1
        if l >= upper:
            return self.bit.e
        r = min(r, upper)
        if l >= r:
            return self.bit.e
        return self.bit.prod(self.starts[l], self.starts[r])


class RangeContourSum(Generic[ValueT]):
    """
    Point-add, range-contour aggregation on a tree.

    For a query ``aggregate(v, l, r)``, this structure aggregates the values of all
    vertices whose distance from ``v`` lies in the half-open interval
    ``[l, r)``. Updates are point additions on single vertices.

    Distance means the number of edges on the path; stored edge weights are
    ignored. The aggregation operation must form a commutative group.

    It is implemented with centroid decomposition. For every centroid, vertices
    in its current component are bucketed by distance from that centroid, and
    inclusion-exclusion removes the overcount from the child component that
    contains the query vertex.

    Space Complexity:
        - ``O(n log n)``

    Complexity Notation:
        ``n`` is the number of vertices.

    Args:
        tree: Tree object used by the data structure or algorithm.
        values: Initial values.
        op: Associative binary operation.
        inv: Inverse operation for the group value.
        e: Identity element for the operation.

    Raises:
        ValueError: If len(values) differs from tree.n.
    """

    def __init__(self, tree: Tree, values: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT], inv: Callable[[ValueT], ValueT], e: ValueT) -> None:
        """Initialize a range-contour sum structure.

        Args:
            tree: Built rooted tree.
            values: Initial vertex values in vertex index order.
            op: Commutative group operation used for aggregation.
            inv: Inverse under ``op``.
            e: Identity element of ``op``.

        Returns:
            None.

        Raises:
            ValueError: If ``len(values)`` is not ``tree.n``.

        Time Complexity:
            O(n log^2 n)
        """
        if len(values) != tree.n:
            raise ValueError('len(values) must be equal to tree.n')
        self.tree = tree
        self.n = tree.n
        self.op = op
        self.inv = inv
        self.e = e
        self.values = list(values)
        self.cdpar = [int(Node(-1))] * self.n
        self._all = [_DepthBuckets([], values, op, inv, e) for _ in range(self.n)]
        self._child: list[dict[int, _DepthBuckets[ValueT]]] = [dict() for _ in range(self.n)]
        self._path: list[list[tuple[int, int, int]]] = [[] for _ in range(self.n)]

        def process_centroid(cd: CentroidDecomposition, centroid: Node) -> None:
            centroid_int = int(centroid)
            self.cdpar[centroid_int] = int(cd.cdpar[centroid])

            child_of = {centroid_int: -1}
            for i in range(len(cd.subtree_idx) - 1):
                start = cd.subtree_idx[i]
                end = cd.subtree_idx[i + 1]
                child = int(cd.dfs_order[start])
                for j in range(start, end):
                    child_of[int(cd.dfs_order[j])] = child

            pairs = sorted((cd.dep[vertex], int(vertex)) for vertex in cd.dfs_order)
            self._all[centroid_int] = _DepthBuckets(pairs, self.values, op, inv, e)

            for vertex in cd.dfs_order:
                self._path[vertex].append((centroid_int, cd.dep[vertex], child_of[int(vertex)]))

        def process_child(cd: CentroidDecomposition, centroid: Node, root: Node, start_idx: int, end_idx: int) -> None:
            pairs = sorted((cd.dep[vertex], int(vertex)) for vertex in cd.dfs_order[start_idx:end_idx])
            self._child[int(centroid)][int(root)] = _DepthBuckets(pairs, self.values, op, inv, e)

        CentroidDecomposition.build_with_callbacks(tree, process_centroid, process_child)

    def add(self, v: int, value: ValueT) -> None:
        """
        Add ``value`` to one vertex.

        Args:
            v: Vertex to update.
            value: Increment under ``op``.

        Returns:
            ``None``.

        Time Complexity:
            O(log^2 n)
        """
        self.values[v] = self.op(self.values[v], value)
        for centroid, _, child_id in self._path[v]:
            self._all[centroid].add_vertex(v, value)
            if child_id != -1:
                self._child[centroid][child_id].add_vertex(v, value)

    def get(self, v: int) -> ValueT:
        """
        Return the current value stored at one vertex.

        Args:
            v: Vertex index.

        Returns:
            Current vertex value.

        Time Complexity:
            O(1)
        """
        return self.values[v]

    def set(self, v: int, value: ValueT) -> None:
        """
        Overwrite one vertex value.

        Args:
            v: Vertex index.
            value: New vertex value.

        Returns:
            ``None``.

        Time Complexity:
            O(log^2 n)
        """
        self.add(v, self.op(value, self.inv(self.values[v])))

    def aggregate(self, v: int, l: int, r: int) -> ValueT:
        """
        Aggregate values on the distance contour around ``v``.

        Args:
            v: Center vertex.
            l: Inclusive lower bound on distance measured in edges.
            r: Exclusive upper bound on distance measured in edges.

        Returns:
            ValueT: Aggregate of all vertices whose path from ``v`` contains
                at least ``l`` and fewer than ``r`` edges.

        Time Complexity:
            O(log^2 n)
        """
        res = self.e
        for centroid, distance, child_id in self._path[v]:
            left = l - distance
            right = r - distance
            res = self.op(res, self._all[centroid].prod_by_depth(left, right))
            if child_id != -1:
                res = self.op(res, self.inv(self._child[centroid][child_id].prod_by_depth(left, right)))
        return res


class RangeContourAdd(Generic[ValueT]):
    """
    Range-contour add and point get on a tree.

    An update ``add(v, l, r, value)`` adds ``value`` to every vertex whose
    distance from ``v`` lies in ``[l, r)``. Queries ask for the value at one
    vertex after all applied contour additions.

    Distance means the number of edges on the path; stored edge weights are
    ignored. The accumulation operation must form a commutative group.

    Space Complexity:
        - ``O(n log n)``

    Complexity Notation:
        ``n`` is the number of vertices.

    Args:
        tree: Tree object used by the data structure or algorithm.
        values: Initial values.
        op: Associative binary operation.
        inv: Inverse operation for the group value.
        e: Identity element for the operation.

    Raises:
        ValueError: If len(values) differs from tree.n.
    """

    def __init__(self, tree: Tree, values: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT], inv: Callable[[ValueT], ValueT], e: ValueT) -> None:
        """Initialize a range-contour add structure.

        Args:
            tree: Built rooted tree.
            values: Initial vertex values in vertex index order.
            op: Commutative group operation used for accumulation.
            inv: Inverse under ``op``.
            e: Identity element of ``op``.

        Returns:
            None.

        Raises:
            ValueError: If ``len(values)`` is not ``tree.n``.

        Time Complexity:
            O(n log n)
        """
        if len(values) != tree.n:
            raise ValueError('len(values) must be equal to tree.n')
        self.tree = tree
        self.n = tree.n
        self.values = list(values)
        self.op = op
        self.inv = inv
        self.e = e
        self.cdpar = [int(Node(-1))] * self.n
        self._all = [GroupRangeAddPointGet(1, op, inv, e) for _ in range(self.n)]
        self._child: list[dict[int, GroupRangeAddPointGet[ValueT]]] = [dict() for _ in range(self.n)]
        self._path: list[list[tuple[int, int, int]]] = [[] for _ in range(self.n)]

        def process_centroid(cd: CentroidDecomposition, centroid: Node) -> None:
            centroid_int = int(centroid)
            self.cdpar[centroid_int] = int(cd.cdpar[centroid])
            max_depth = max(cd.dep[vertex] for vertex in cd.dfs_order)
            self._all[centroid_int] = GroupRangeAddPointGet(max_depth + 1, op, inv, e)

            child_of = {centroid_int: -1}
            for i in range(len(cd.subtree_idx) - 1):
                start = cd.subtree_idx[i]
                end = cd.subtree_idx[i + 1]
                child = int(cd.dfs_order[start])
                for j in range(start, end):
                    child_of[int(cd.dfs_order[j])] = child

            for vertex in cd.dfs_order:
                self._path[vertex].append((centroid_int, cd.dep[vertex], child_of[int(vertex)]))

        def process_child(cd: CentroidDecomposition, centroid: Node, root: Node, start_idx: int, end_idx: int) -> None:
            max_depth = max(cd.dep[vertex] for vertex in cd.dfs_order[start_idx:end_idx])
            self._child[int(centroid)][int(root)] = GroupRangeAddPointGet(max_depth + 1, op, inv, e)

        CentroidDecomposition.build_with_callbacks(tree, process_centroid, process_child)

    def add(self, v: int, l: int, r: int, value: ValueT) -> None:
        """
        Add ``value`` to every vertex at distance in ``[l, r)`` from ``v``.

        Args:
            v: Center vertex of the contour update.
            l: Inclusive lower bound on distance measured in edges.
            r: Exclusive upper bound on distance measured in edges.
            value: Increment applied to each target vertex.

        Returns:
            ``None``.

        Time Complexity:
            O(log^2 n)
        """
        for centroid, distance, child_id in self._path[v]:
            left = max(0, l - distance)
            right = min(r - distance, self._all[centroid].n)
            if left < right:
                self._all[centroid].range_add(left, right, value)
            if child_id != -1:
                child = self._child[centroid][child_id]
                left = max(0, l - distance)
                right = min(r - distance, child.n)
                if left < right:
                    child.range_add(left, right, value)

    def get(self, v: int) -> ValueT:
        """
        Return the current value stored at one vertex.

        Args:
            v: Vertex index.

        Returns:
            Current vertex value.

        Time Complexity:
            O(log^2 n)
        """
        res = self.values[v]
        for centroid, distance, child_id in self._path[v]:
            res = self.op(res, self._all[centroid].get(distance))
            if child_id != -1:
                res = self.op(res, self.inv(self._child[centroid][child_id].get(distance)))
        return res


__all__ = [
    'DSUOnTree',
    'VirtualTreeResult',
    'VirtualTreeBuilder',
    'TreePathQuery',
    'RangeContourSum',
    'RangeContourAdd',
]
