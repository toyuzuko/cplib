"""Static tree preprocessing: heavy-light and centroid decompositions, and LCA."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from cplib.datastructure.sparsetable import SparseTable
from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.tools.type import T

__all__ = ['HeavyLightDecomposition', 'CentroidDecomposition', 'SparseTableLCA', 'LinearTimeLCA']


class HeavyLightDecomposition:
    """
    Heavy-light decomposition of a built rooted tree.

    This structure linearizes the vertices of a rooted tree so that:

    - every rooted subtree becomes one contiguous half-open interval, and
    - every simple path can be decomposed into ``O(log n)`` contiguous segments.

    It exposes the standard arrays used by competitive-programming HLD code:

    - ``id[v]``:
      position of vertex ``v`` in heavy-light order.
    - ``rev[i]``:
      inverse map from heavy-light order back to the original vertex.
    - ``top[v]``:
      head vertex of the heavy path containing ``v``.
    - ``nxt[v]``:
      heavy child of ``v``, or ``-1`` if none exists.

    These arrays are typically used together with a Fenwick tree or segment
    tree placed on heavy-light order. Vertex IDs use ``Node``; positions and
    interval endpoints in heavy-light order use ``int``. The tree's edges
    and root must remain unchanged while this decomposition is in use.

    Space Complexity:
        - ``O(n)``

    Complexity Notation:
        ``n`` is the number of vertices.

    Args:
        tree: Tree object used by the data structure or algorithm.

    Raises:
        ValueError: If tree has not been built.

    Examples:
        >>> tree = Tree(3)
        >>> tree.add_edge(Node(0), Node(1))
        >>> tree.add_edge(Node(1), Node(2))
        >>> tree.build(Node(2))
        >>> hld = HeavyLightDecomposition(tree)
        >>> hld.get_vertex(0)
        2
        >>> hld.lca(Node(0), Node(1))
        1
        >>> hld.convert_array(['a', 'b', 'c'])
        ['c', 'b', 'a']
        >>> hld.subtree_range(Node(1))
        (1, 3)
        >>> list(hld.path_ranges(Node(0), Node(2)))
        [(0, 3)]
        >>> list(hld.path_ranges(Node(0), Node(2), edge_query=True))
        [(1, 3)]
        >>> list(hld.path_ranges(Node(0), Node(0), edge_query=True))
        [(3, 3)]
    """

    def __init__(self, tree: Tree) -> None:
        """Build the heavy-light decomposition of one rooted tree.

        Args:
            tree: Built rooted tree.

        Returns:
            None.

        Raises:
            ValueError: If ``tree`` has not been built yet.

        Time Complexity:
            O(n)
        """
        if tree.root == -1:
            raise ValueError('This tree has not been built yet')
        self.tree = tree
        self.n = tree.n
        self.id = [-1] * self.n
        self.top = [Node(-1)] * self.n
        self.top[tree.root] = tree.root
        self.nxt = [Node(-1)] * self.n
        self.rev = [Node(-1)] * self.n
        self._id = self.id
        self._top = self.top
        self._nxt = self.nxt
        self._rev = self.rev
        stack = [tree.root]
        cnt = 0
        while stack:
            v = stack.pop()
            self.id[v] = cnt
            self.rev[cnt] = v
            cnt += 1
            max_sz = 0
            for a, _ in tree.tree[v]:
                if a == tree.par_v[v]:
                    continue
                if max_sz < tree.size[a]:
                    max_sz = tree.size[a]
                    self.nxt[v] = a
            for a, _ in tree.tree[v]:
                if a == tree.par_v[v] or self.nxt[v] == a:
                    continue
                self.top[a] = a
                stack.append(a)
            if self.nxt[v] != -1:
                self.top[self.nxt[v]] = self.top[v]
                stack.append(self.nxt[v])

    def lca(self, u: Node, v: Node) -> Node:
        """
        Return the lowest common ancestor of two vertices.

        Args:
            u: First vertex.
            v: Second vertex.

        Returns:
            Node: Original vertex ID of the lowest common ancestor.

        Time Complexity:
            O(log n)
        """
        while True:
            if self.id[u] > self.id[v]:
                u, v = v, u
            if self.top[u] == self.top[v]:
                return u
            v = self.tree.par_v[self.top[v]]

    def path_ranges(self, u: Node, v: Node, edge_query: bool = False) -> Iterator[tuple[int, int]]:
        """
        Yield heavy-light intervals covering the path from ``u`` to ``v``.

        The intervals cover the simple path without overlap. Their emission
        order and the increasing positions within each interval do not
        necessarily follow ``u -> v``. Use them for commutative aggregation
        or updates whose result does not depend on traversal order. For a
        directional, non-commutative fold, use ``TreePathQuery.path_prod``.

        In edge-query mode, each edge is stored at its child vertex's position
        relative to the built root. The LCA's position is excluded. The final
        interval can be empty; in particular, ``u == v`` yields one empty
        interval in edge-query mode.

        Args:
            u: One endpoint of the path.
            v: The other endpoint of the path.
            edge_query: Whether to encode the path as vertex intervals or edge
                intervals.

        Yields:
            tuple[int, int]: Half-open interval ``[l, r)`` in heavy-light order.

        Time Complexity:
            O(log n) to consume all intervals.

        Space Complexity:
            O(1) auxiliary space; collecting the intervals uses O(log n).
        """
        while True:
            if self.id[u] > self.id[v]:
                u, v = v, u
            if self.top[u] == self.top[v]:
                yield self.id[u] + edge_query, self.id[v] + 1
                return
            yield self.id[self.top[v]], self.id[v] + 1
            v = self.tree.par_v[self.top[v]]

    def subtree_range(self, v: Node) -> tuple[int, int]:
        """
        Return the half-open interval corresponding to one rooted subtree.

        Args:
            v: Root of the queried subtree.

        Returns:
            tuple[int, int]: Interval ``[l, r)`` such that the subtree of ``v``
            is exactly the vertices whose heavy-light positions lie in that range.
            The root is the one used when building the original tree. For
            edges wholly inside this subtree, use ``[l + 1, r)`` with each
            edge stored at its child vertex's position.

        Time Complexity:
            O(1)
        """
        return self.id[v], self.id[v] + self.tree.size[v]

    def dist(self, u: Node, v: Node) -> int:
        """
        Return the weighted distance between two vertices.

        Args:
            u: First vertex.
            v: Second vertex.

        Returns:
            int: Sum of edge weights on the path from ``u`` to ``v``.

        Time Complexity:
            O(log n)
        """
        return self.tree.cost[u] + self.tree.cost[v] - 2 * self.tree.cost[self.lca(u, v)]

    def hops(self, u: Node, v: Node) -> int:
        """
        Return the number of edges on the path between two vertices.

        Args:
            u: First vertex.
            v: Second vertex.

        Returns:
            int: Number of edges on the path from ``u`` to ``v``.

        Time Complexity:
            O(log n)
        """
        return self.tree.dep[u] + self.tree.dep[v] - 2 * self.tree.dep[self.lca(u, v)]

    def convert_array(self, arr: list[T]) -> list[T]:
        """
        Permute a vertex-indexed array into heavy-light order.

        Args:
            arr: Array indexed by original vertex id.

        Returns:
            list[T]: Array reordered so index ``i`` corresponds to ``rev[i]``.

        Time Complexity:
            O(n)
        """
        return [arr[self.rev[i]] for i in range(self.n)]

    def get_vertex(self, i: int) -> Node:
        """
        Return the original vertex stored at one heavy-light position.

        Args:
            i: Position in heavy-light order, in ``[0, n)``.

        Returns:
            Node: Original vertex ID stored at position ``i``.

        Time Complexity:
            O(1)
        """
        return self.rev[i]


class CentroidDecomposition:
    """
    Centroid decomposition of a static tree.

    The decomposition recursively chooses one centroid for each remaining
    component and records the parent relation in the centroid tree. The fields
    exposed by this class are intended to support centroid-based data
    structures, especially those that need DFS order slices inside each
    decomposed component.

    Attributes:
        tree: Original tree.
        n: Number of vertices.
        cdpar: Parent of each vertex in the centroid tree, or ``-1`` for the
            centroid-tree root.
        used: Whether a vertex has already been selected as a centroid.
        size: Temporary subtree sizes inside the current undecomposed component.
        par: Temporary parent array inside the current undecomposed component.
        dep: Temporary distance from the current component root.

    Space Complexity:
        - ``O(n)``

    Complexity Notation:
        ``n`` is the number of vertices.

    Args:
        tree: Tree object used by the data structure or algorithm.
    """

    def __init__(self, tree: Tree) -> None:
        """Build the centroid decomposition of one rooted tree.

        Args:
            tree: Built rooted tree to decompose.

        Returns:
            None.

        Time Complexity:
            O(n log n)
        """
        self.tree = tree
        self.n = tree.n
        self.cdpar = [Node(-1)] * self.n
        self.used = [False] * self.n
        self.size = [1] * self.n
        self.par = [Node(-1)] * self.n
        self.dep = [0] * self.n
        self._used = self.used
        self._size = self.size
        self._par = self.par
        self._dep = self.dep
        self._dfs(Node(0))
        stack = [self._get_centroid(Node(0))]
        while stack:
            v = stack.pop()
            self.used[v] = True
            self._dfs(v)
            for a in self._unused_child(v):
                self.cdpar[c := self._get_centroid(a)] = v
                stack.append(c)

    def _get_centroid(self, v: Node) -> Node:
        if self.size[v] <= 2:
            return v
        half = self.size[v] // 2
        while True:
            for a in self._unused_child(v):
                if self.size[a] > half:
                    v = a
                    break
            else:
                return v

    def _unused_child(self, v: Node) -> Iterator[Node]:
        for a, _ in self.tree.tree[v]:
            if self.par[v] == a or self.used[a]:
                continue
            yield a

    def _dfs(self, r: Node) -> None:
        self.par[r] = Node(-1)
        self.size[r] = 1
        self.dep[r] = 0
        self.dfs_order: list[Node] = []
        self.subtree_idx: list[int] = []
        stack = [r]
        while stack:
            v = stack.pop()
            self.dfs_order.append(v)
            if self.par[v] == r:
                self.subtree_idx.append(len(self.dfs_order) - 1)
            for a in reversed(tuple(self._unused_child(v))):
                self.par[a] = v
                self.size[a] = 1
                self.dep[a] = self.dep[v] + 1
                stack.append(a)
        self.subtree_idx.append(len(self.dfs_order))
        for v in self.dfs_order[::-1]:
            for a in self._unused_child(v):
                self.size[v] += self.size[a]

    @classmethod
    def build_with_callbacks(
        cls,
        tree: Tree,
        process_centroid: Callable[['CentroidDecomposition', Node], None],
        process_child: Callable[['CentroidDecomposition', Node, Node, int, int], None],
    ) -> 'CentroidDecomposition':
        """
        Build a centroid decomposition while invoking callbacks.

        This alternate constructor is intended for centroid-based data
        structures that need to preprocess each centroid component.

        Args:
            tree: Built rooted tree to decompose.
            process_centroid: Callback invoked once for every chosen centroid
                after the current component has been traversed. The arguments
                are the partially built decomposition object and the centroid
                vertex.
            process_child: Callback invoked once for every child component
                hanging from the current centroid. Its arguments are:
                1. the decomposition object,
                2. the current centroid vertex,
                3. the root vertex of that child component in the current DFS,
                4. the start index of that component in ``cd.dfs_order``,
                5. the exclusive end index in ``cd.dfs_order``.
                Temporary arrays such as ``cd.dfs_order``, ``cd.subtree_idx``,
                ``cd.dep``, ``cd.par``, and ``cd.size`` describe only the
                current component and are overwritten by later decompositions.

        Returns:
            CentroidDecomposition: Constructed decomposition object.

        Time Complexity:
            ``O(n log n)`` plus the total cost of all callback invocations.
        """
        cd = cls.__new__(cls)
        cd.tree = tree
        cd.n = tree.n
        cd.cdpar = [Node(-1)] * cd.n
        cd.used = [False] * cd.n
        cd.size = [1] * cd.n
        cd.par = [Node(-1)] * cd.n
        cd.dep = [0] * cd.n
        cd._used = cd.used
        cd._size = cd.size
        cd._par = cd.par
        cd._dep = cd.dep
        cd._dfs(Node(0))
        stack = [cd._get_centroid(Node(0))]
        while stack:
            v = stack.pop()
            cd.used[v] = True
            cd._dfs(v)
            process_centroid(cd, v)
            for i, a in enumerate(cd._unused_child(v)):
                process_child(cd, v, a, cd.subtree_idx[i], cd.subtree_idx[i + 1])
                cd.cdpar[c := cd._get_centroid(a)] = v
                stack.append(c)
        return cd


class SparseTableLCA:
    """
    Lowest common ancestor by Euler tour and sparse table.

    This structure performs one Euler tour of a built rooted tree and answers
    lowest common ancestor queries in ``O(1)`` time via a range-minimum query
    over depths.

    Compared with :class:`HeavyLightDecomposition`, preprocessing is
    ``O(n log n)`` instead of ``O(n)``, but each LCA query is ``O(1)``. In
    Python this is often still practical when the tree is static and the number
    of LCA queries is large.

    Space Complexity:
        - ``O(n log n)``

    Complexity Notation:
        ``n`` is the number of vertices.

    Args:
        tree: Tree object used by the data structure or algorithm.

    Raises:
        ValueError: If tree has not been built.
    """

    def __init__(self, tree: Tree) -> None:
        """Build an Euler-tour LCA structure for one rooted tree.

        Args:
            tree: Built rooted tree.

        Returns:
            None.

        Raises:
            ValueError: If ``tree`` has not been built yet.

        Time Complexity:
            O(n log n)
        """
        if tree.root == -1:
            raise ValueError('This tree has not been built yet')
        self.tree = tree
        self.n = tree.n
        self.first = [-1] * self.n
        tour: list[tuple[int, int]] = []
        stack: list[tuple[int, int, int]] = [(int(tree.root), -1, 0)]
        while stack:
            vertex, parent, state = stack.pop()
            if state == 0:
                if self.first[vertex] == -1:
                    self.first[vertex] = len(tour)
                tour.append((tree.dep[vertex], vertex))
                stack.append((vertex, parent, 1))
                for to, _ in reversed(tree.tree[vertex]):
                    if to == parent:
                        continue
                    stack.append((int(to), vertex, 0))
            else:
                if parent != -1:
                    tour.append((tree.dep[parent], parent))
        self._st = SparseTable(tour, min)

    def lca(self, u: Node, v: Node) -> int:
        """
        Return the lowest common ancestor of two vertices.

        Args:
            u: First vertex or endpoint index.
            v: Second vertex or endpoint index.

        Returns:
            Index of the lowest common ancestor with respect to the tree root.

        Time Complexity:
            O(1)
        """
        left = self.first[u]
        right = self.first[v]
        if left > right:
            left, right = right, left
        return self._st.prod(left, right + 1)[1]

    def dist(self, u: Node, v: Node) -> int:
        """
        Return the weighted distance between two vertices.

        Args:
            u: First vertex or endpoint index.
            v: Second vertex or endpoint index.

        Returns:
            Sum of edge weights on the unique path between u and v.

        Time Complexity:
            O(1)
        """
        return self.tree.cost[u] + self.tree.cost[v] - 2 * self.tree.cost[self.lca(u, v)]

    def hops(self, u: Node, v: Node) -> int:
        """
        Return the number of edges on the path between two vertices.

        Args:
            u: First vertex or endpoint index.
            v: Second vertex or endpoint index.

        Returns:
            Number of edges on the unique path between u and v.

        Time Complexity:
            O(1)
        """
        return self.tree.dep[u] + self.tree.dep[v] - 2 * self.tree.dep[self.lca(u, v)]


class LinearTimeLCA:
    """
    Lowest common ancestor by ``±1`` RMQ in linear preprocessing time.

    This is a Farach-Colton and Bender style implementation. It performs an
    Euler tour of the tree, splits the depth sequence into small blocks, solves
    intra-block RMQ by lookup tables on block patterns, and solves inter-block
    RMQ with a sparse table on block minima.

    The preprocessing runs in ``O(n)`` time by choosing the block size around
    ``log n / 2``. Queries are answered in ``O(1)`` time.

    Space Complexity:
        - ``O(n)``

    Complexity Notation:
        ``n`` is the number of vertices.

    Args:
        tree: Tree object used by the data structure or algorithm.

    Raises:
        ValueError: If tree has not been built.
    """

    _lookup_cache: dict[int, list[list[int]]] = {}

    def __init__(self, tree: Tree) -> None:
        """Build a linear-time LCA structure for one rooted tree.

        Args:
            tree: Built rooted tree.

        Returns:
            None.

        Raises:
            ValueError: If ``tree`` has not been built yet.

        Time Complexity:
            O(n)
        """
        if tree.root == -1:
            raise ValueError('This tree has not been built yet')
        self.tree = tree
        self.n = tree.n
        self.first = [-1] * self.n
        tour_vertices: list[int] = []
        depths: list[int] = []
        stack: list[tuple[int, int, int]] = [(int(tree.root), -1, 0)]
        while stack:
            vertex, parent, state = stack.pop()
            if state == 0:
                if self.first[vertex] == -1:
                    self.first[vertex] = len(depths)
                tour_vertices.append(vertex)
                depths.append(tree.dep[vertex])
                stack.append((vertex, parent, 1))
                for to, _ in reversed(tree.tree[vertex]):
                    if to == parent:
                        continue
                    stack.append((int(to), vertex, 0))
            elif parent != -1:
                tour_vertices.append(parent)
                depths.append(tree.dep[parent])
        self.euler = tour_vertices
        self.depths = depths
        m = len(depths)
        self.block_size = max(1, m.bit_length() // 2)
        block_size = self.block_size
        block_cnt = (m + block_size - 1) // block_size
        pad = block_cnt * block_size - m
        if pad:
            last_depth = depths[-1]
            depths = depths + [last_depth + i + 1 for i in range(pad)]
            tour_vertices = tour_vertices + [-1] * pad
        self.block_pattern = [0] * block_cnt
        self.block_min_index = [0] * block_cnt
        block_mins: list[tuple[int, int]] = []
        lookup = self._get_lookup(block_size)
        for block in range(block_cnt):
            start = block * block_size
            pattern = 0
            best = start
            for i in range(block_size - 1):
                if depths[start + i + 1] > depths[start + i]:
                    pattern |= 1 << i
                elif depths[start + i + 1] < depths[best]:
                    best = start + i + 1
            self.block_pattern[block] = pattern
            self.block_min_index[block] = best
            block_mins.append((depths[best], best))
        self._tour_vertices_padded = tour_vertices
        self._depths_padded = depths
        self._lookup = lookup
        self._block_st = SparseTable(block_mins, min)

    @classmethod
    def _get_lookup(cls, block_size: int) -> list[list[int]]:
        cached = cls._lookup_cache.get(block_size)
        if cached is not None:
            return cached
        patterns = 1 << max(0, block_size - 1)
        lookup = [[0] * (block_size * block_size) for _ in range(patterns)]
        for pattern in range(patterns):
            rel_depth = [0] * block_size
            for i in range(block_size - 1):
                rel_depth[i + 1] = rel_depth[i] + (1 if (pattern >> i) & 1 else -1)
            table = lookup[pattern]
            for l in range(block_size):
                best = l
                base = l * block_size
                table[base + l] = l
                for r in range(l + 1, block_size):
                    if rel_depth[r] < rel_depth[best]:
                        best = r
                    table[base + r] = best
        cls._lookup_cache[block_size] = lookup
        return lookup

    def _block_argmin(self, block: int, left: int, right: int) -> int:
        pattern = self.block_pattern[block]
        return block * self.block_size + self._lookup[pattern][left * self.block_size + right]

    def _rmq_index(self, left: int, right: int) -> int:
        block_size = self.block_size
        bl = left // block_size
        br = right // block_size
        if bl == br:
            return self._block_argmin(bl, left % block_size, right % block_size)
        candidates = [
            self._block_argmin(bl, left % block_size, block_size - 1),
            self._block_argmin(br, 0, right % block_size),
        ]
        if bl + 1 <= br - 1:
            candidates.append(self._block_st.prod(bl + 1, br)[1])
        best = candidates[0]
        for idx in candidates[1:]:
            if self._depths_padded[idx] < self._depths_padded[best]:
                best = idx
        return best

    def lca(self, u: Node, v: Node) -> int:
        """
        Return the lowest common ancestor of two vertices.

        Args:
            u: First vertex or endpoint index.
            v: Second vertex or endpoint index.

        Returns:
            Index of the lowest common ancestor with respect to the tree root.

        Time Complexity:
            O(1)
        """
        left = self.first[u]
        right = self.first[v]
        if left > right:
            left, right = right, left
        return self._tour_vertices_padded[self._rmq_index(left, right)]

    def dist(self, u: Node, v: Node) -> int:
        """
        Return the weighted distance between two vertices.

        Args:
            u: First vertex or endpoint index.
            v: Second vertex or endpoint index.

        Returns:
            Sum of edge weights on the unique path between u and v.

        Time Complexity:
            O(1)
        """
        return self.tree.cost[u] + self.tree.cost[v] - 2 * self.tree.cost[self.lca(u, v)]

    def hops(self, u: Node, v: Node) -> int:
        """
        Return the number of edges on the path between two vertices.

        Args:
            u: First vertex or endpoint index.
            v: Second vertex or endpoint index.

        Returns:
            Number of edges on the unique path between u and v.

        Time Complexity:
            O(1)
        """
        return self.tree.dep[u] + self.tree.dep[v] - 2 * self.tree.dep[self.lca(u, v)]
