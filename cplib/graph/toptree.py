"""Static and self-adjusting top trees with shared tree-DP callbacks.

Algorithmic references:
    Tarjan and Werneck, Self-Adjusting Top Trees (SODA 2005).
    https://www.cs.princeton.edu/techreports/2006/750.pdf
    https://ei1333.github.io/library/structure/dynamic-tree/top-tree.hpp.html

The array representation and public forest operations follow cplib's link-cut
implementation. Virtual contributions are stored in separate rake splay trees;
path rotations transfer their branch handles when the auxiliary root changes.
"""

from collections.abc import Callable, Sequence
from typing import Generic

from cplib.graph.core import Tree
from cplib.tools.type import ValueT, VertexValueT, EdgeValueT, PointT, PathT

__all__ = ['TopTree', 'StaticTopTree', 'TopTreeWithEdges', 'StaticTopTreeWithEdges']


class TopTree(Generic[ValueT, PointT, PathT]):
    """Maintain tree DP on a forest under links, cuts, and point updates.

    Preferred paths are compress splay trees. Each vertex also owns a rake
    splay tree of its virtual branches. Unlike RerootingLinkCutTree,
    removing a branch needs no inverse: ``rake`` may be any commutative monoid,
    including maximum. ``compress`` is associative and preserves path order.

    The callbacks must describe a consistent tree DP: changing the preferred
    paths or parenthesization must not change the represented answer. Mere
    associativity of unrelated callbacks is insufficient. ``add_vertex``
    constructs a one-vertex path cluster with its virtual branches attached;
    ``add_edge`` turns a path cluster into a contribution at its parent.
    A one-vertex cluster is unchanged by path reversal. Callbacks must not
    mutate their arguments; returned aggregates may be shared internally.

    ``path_cluster_value`` includes off-path branches. The callback definition
    may ignore those branches to implement a path-only product. No lazy range
    updates are provided. Use TopTreeWithEdges to manage vertex and edge
    payloads separately; it represents edges by additional internal vertices.

    Args:
        values: Initial vertex payloads; indices are fixed in ``[0, n)``.
        point_identity: Identity of ``rake`` for a vertex with no virtual children.
        add_vertex: Maps ``(branch_aggregate, vertex_value)`` to a path cluster.
        add_edge: Converts a path cluster to a parent-side point contribution.
        rake: Commutative associative merge of point contributions.
        compress: Associative concatenation of upper and lower path clusters.

    Space Complexity:
        O(n), assuming O(1)-size payloads and aggregates. Rake slots are reused
        and never grow with the number of queries.

    Examples:
        Maintain the maximum of non-negative vertex values, without an inverse:

        >>> tree = TopTree([2, 7, 3], 0, max, lambda path: path, max, max)
        >>> tree.link(child=1, parent=0)
        >>> tree.link(child=2, parent=1)
        >>> tree.tree_value(0)
        7
        >>> tree.set(1, 1)
        >>> tree.tree_value(0)
        3
        >>> tree.subtree_value(1)
        3
        >>> tree.cut(1, 2)
        >>> tree.tree_value(0), tree.tree_value(2)
        (2, 3)
    """

    __slots__ = ('n', '_values', '_point_identity', '_add_vertex', '_add_edge', '_rake', '_compress', '_left', '_right', '_parent', '_rev', '_key', '_forward', '_backward', '_light', '_belong', '_r_left', '_r_right', '_r_parent', '_r_key', '_r_sum', '_free')

    def __init__(self, values: Sequence[ValueT], point_identity: PointT, add_vertex: Callable[[PointT, ValueT], PathT], add_edge: Callable[[PathT], PointT], rake: Callable[[PointT, PointT], PointT], compress: Callable[[PathT, PathT], PathT]) -> None:
        """Create an isolated vertex for each initial payload.

        Args:
            values: Initial vertex payloads, including an empty sequence.
            point_identity: Identity element for virtual-branch aggregation.
            add_vertex: Callback ``(point, value) -> path``.
            add_edge: Callback ``path -> point``.
            rake: Commutative point-cluster merge, with no inverse required.
            compress: Ordered path-cluster concatenation.

        Returns:
            None.

        Time Complexity:
            O(n), assuming O(1) callbacks.
        """
        self.n = n = len(values)
        self._values = list(values)
        self._point_identity = point_identity
        self._add_vertex = add_vertex
        self._add_edge = add_edge
        self._rake = rake
        self._compress = compress
        self._left = [-1] * n
        self._right = [-1] * n
        self._parent = [-1] * n
        self._rev = [False] * n
        self._key = [add_vertex(point_identity, value) for value in values]
        self._forward = self._key[:]
        self._backward = self._key[:]
        self._light = [-1] * n
        self._belong = [-1] * n
        self._r_left: list[int] = []
        self._r_right: list[int] = []
        self._r_parent: list[int] = []
        self._r_key: list[PointT] = []
        self._r_sum: list[PointT] = []
        self._free: list[int] = []

    def _pull(self, vertex: int) -> None:
        forward = backward = self._key[vertex]
        left = self._left[vertex]
        right = self._right[vertex]
        compress = self._compress
        if left != -1:
            forward = compress(self._forward[left], forward)
            backward = compress(backward, self._backward[left])
        if right != -1:
            forward = compress(forward, self._forward[right])
            backward = compress(self._backward[right], backward)
        self._forward[vertex] = forward
        self._backward[vertex] = backward

    def _toggle(self, vertex: int) -> None:
        self._left[vertex], self._right[vertex] = self._right[vertex], self._left[vertex]
        self._forward[vertex], self._backward[vertex] = self._backward[vertex], self._forward[vertex]
        self._rev[vertex] = not self._rev[vertex]

    def _push(self, vertex: int) -> None:
        if self._rev[vertex]:
            left = self._left[vertex]
            right = self._right[vertex]
            if left != -1:
                self._toggle(left)
            if right != -1:
                self._toggle(right)
            self._rev[vertex] = False

    def _rotate(self, vertex: int) -> None:
        left, right, parent = self._left, self._right, self._parent
        p = parent[vertex]
        g = parent[p]
        if left[p] == vertex:
            middle = right[vertex]
            right[vertex] = p
            left[p] = middle
        else:
            middle = left[vertex]
            left[vertex] = p
            right[p] = middle
        if middle != -1:
            parent[middle] = p
        parent[p] = vertex
        parent[vertex] = g
        if g != -1:
            if left[g] == p:
                left[g] = vertex
            elif right[g] == p:
                right[g] = vertex
        # The promoted node is pulled once at the end of its splay. Every
        # demoted node already has its final children for this rotation.
        self._pull(p)

    def _splay(self, vertex: int) -> None:
        left, right, parent = self._left, self._right, self._parent
        stack = [vertex]
        current = vertex
        while True:
            p = parent[current]
            if p == -1 or (left[p] != current and right[p] != current):
                break
            current = p
            stack.append(current)
        if current == vertex:
            self._push(vertex)
            return
        self._belong[vertex] = self._belong[current]
        self._belong[current] = -1
        for current in reversed(stack):
            self._push(current)
        while True:
            p = parent[vertex]
            if p == -1 or (left[p] != vertex and right[p] != vertex):
                break
            g = parent[p]
            if g != -1 and (left[g] == p or right[g] == p):
                if (left[p] == vertex) == (left[g] == p):
                    self._rotate(p)
                else:
                    self._rotate(vertex)
            self._rotate(vertex)
        self._pull(vertex)

    def _r_pull(self, node: int) -> None:
        value = self._r_key[node]
        left = self._r_left[node]
        right = self._r_right[node]
        if left != -1:
            value = self._rake(self._r_sum[left], value)
        if right != -1:
            value = self._rake(value, self._r_sum[right])
        self._r_sum[node] = value

    def _r_rotate(self, node: int) -> None:
        left, right, parent = self._r_left, self._r_right, self._r_parent
        p = parent[node]
        g = parent[p]
        if left[p] == node:
            middle = right[node]
            right[node] = p
            left[p] = middle
        else:
            middle = left[node]
            left[node] = p
            right[p] = middle
        if middle != -1:
            parent[middle] = p
        parent[p] = node
        parent[node] = g
        if g != -1:
            if left[g] == p:
                left[g] = node
            else:
                right[g] = node
        self._r_pull(p)

    def _r_splay(self, node: int) -> None:
        parent, left = self._r_parent, self._r_left
        if parent[node] == -1:
            return
        while parent[node] != -1:
            p = parent[node]
            g = parent[p]
            if g != -1:
                if (left[p] == node) == (left[g] == p):
                    self._r_rotate(p)
                else:
                    self._r_rotate(node)
            self._r_rotate(node)
        self._r_pull(node)

    def _r_insert(self, root: int, value: PointT) -> int:
        if self._free:
            node = self._free.pop()
            self._r_key[node] = value
            self._r_sum[node] = value
        else:
            node = len(self._r_parent)
            self._r_left.append(-1)
            self._r_right.append(-1)
            self._r_parent.append(-1)
            self._r_key.append(value)
            self._r_sum.append(value)
        # Rake is unordered, so a new root can be attached without a key search.
        self._r_left[node] = root
        if root != -1:
            self._r_parent[root] = node
            self._r_sum[node] = self._rake(self._r_sum[root], value)
        return node

    def _r_remove(self, node: int) -> int:
        self._r_splay(node)
        left = self._r_left[node]
        right = self._r_right[node]
        if left != -1:
            self._r_parent[left] = -1
        if right != -1:
            self._r_parent[right] = -1
        if left == -1:
            root = right
        elif right == -1:
            root = left
        else:
            root = left
            while self._r_right[root] != -1:
                root = self._r_right[root]
            self._r_splay(root)
            self._r_right[root] = right
            self._r_parent[right] = root
            self._r_pull(root)
        self._r_left[node] = self._r_right[node] = self._r_parent[node] = -1
        self._r_key[node] = self._r_sum[node] = self._point_identity
        self._free.append(node)
        return root

    def _access(self, vertex: int) -> int:
        last = -1
        current = vertex
        while current != -1:
            self._splay(current)
            right = self._right[current]
            if right != last:
                branch = self._light[current]
                if last != -1:
                    node = self._belong[last]
                    self._belong[last] = -1
                    if right != -1:
                        # Exchange the promoted and demoted branches in one
                        # rake slot instead of deleting and inserting nodes.
                        self._r_splay(node)
                        self._r_key[node] = self._add_edge(self._forward[right])
                        self._r_pull(node)
                        self._belong[right] = node
                        branch = node
                    else:
                        branch = self._r_remove(node)
                elif right != -1:
                    branch = self._r_insert(branch, self._add_edge(self._forward[right]))
                    self._belong[right] = branch
                self._light[current] = branch
                point = self._point_identity if branch == -1 else self._r_sum[branch]
                self._key[current] = self._add_vertex(point, self._values[current])
                self._right[current] = last
                if last != -1:
                    self._parent[last] = current
                self._pull(current)
            last = current
            current = self._parent[current]
        if last != vertex:
            self._splay(vertex)
        return last

    def access(self, vertex: int) -> int:
        """Expose the path from the represented root to ``vertex``.

        The represented root is preserved; vertex becomes the auxiliary root.

        Args:
            vertex: Vertex index.

        Returns:
            Last vertex processed while joining preferred paths, as in
            RerootingLinkCutTree.access; not necessarily the tree root.

        Raises:
            IndexError: If vertex is outside ``[0, n)``.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        return self._access(vertex)

    def reroot(self, vertex: int) -> None:
        """Make vertex the represented-tree root.

        Args:
            vertex: New root vertex.

        Returns:
            None.

        Raises:
            IndexError: If vertex is outside ``[0, n)``.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        self._access(vertex)
        self._toggle(vertex)

    def link(self, child: int, parent: int) -> None:
        """Reroot the child's component and attach it under parent.

        The parent's original root is preserved. Rejected operations preserve
        topology, payloads, and represented roots.

        Args:
            child: Endpoint in the component to reroot before attaching.
            parent: Endpoint in a different component whose root is retained.

        Returns:
            None.

        Raises:
            IndexError: If either vertex is outside ``[0, n)``.
            ValueError: If the vertices are already connected.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not (0 <= child < self.n and 0 <= parent < self.n):
            raise IndexError('vertex index out of range')
        if child == parent:
            raise ValueError('link requires different components')
        self._access(child)
        self._access(parent)
        if self._parent[child] != -1:
            raise ValueError('link requires different components')
        self._toggle(child)
        self._parent[child] = parent
        self._right[parent] = child
        self._pull(parent)

    def cut(self, u: int, v: int) -> None:
        """Cut an existing edge, with either endpoint order.

        The resulting trees are rooted at u and v. Failed operations preserve
        topology, payloads, and represented roots.

        Args:
            u: First edge endpoint.
            v: Second edge endpoint.

        Returns:
            None.

        Raises:
            IndexError: If either vertex is outside ``[0, n)``.
            ValueError: If the edge does not exist.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        if u == v:
            raise ValueError('edge does not exist')
        self._access(u)
        self._access(v)
        self._splay(u)
        if self._right[u] == v:
            self._push(v)
            if self._left[v] != -1:
                raise ValueError('edge does not exist')
            self._right[u] = -1
            self._parent[v] = -1
            self._pull(u)
            self._toggle(u)
        elif self._parent[u] == v and self._left[u] == -1:
            branch = self._r_remove(self._belong[u])
            self._light[v] = branch
            self._belong[u] = -1
            self._parent[u] = -1
            point = self._point_identity if branch == -1 else self._r_sum[branch]
            self._key[v] = self._add_vertex(point, self._values[v])
            self._pull(v)
            self._toggle(v)
        else:
            raise ValueError('edge does not exist')

    def cut_parent(self, child: int) -> None:
        """Detach child from its current parent.

        Child becomes a root; the parent's component keeps its root.
        Rejected cuts preserve topology, payloads, and represented roots.

        Args:
            child: Vertex whose parent edge is removed.

        Returns:
            None.

        Raises:
            IndexError: If child is outside ``[0, n)``.
            ValueError: If child is already a root.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not 0 <= child < self.n:
            raise IndexError('vertex index out of range')
        self._access(child)
        left = self._left[child]
        if left == -1:
            raise ValueError('child must not be a root')
        self._parent[left] = -1
        self._left[child] = -1
        self._pull(child)

    def same(self, u: int, v: int) -> bool:
        """Test connectivity while preserving represented roots.

        Args:
            u: First vertex.
            v: Second vertex.

        Returns:
            Whether the vertices belong to the same tree.

        Raises:
            IndexError: If either vertex is outside ``[0, n)``.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        if u == v:
            return True
        self._access(u)
        self._access(v)
        return self._parent[u] != -1

    def root(self, vertex: int) -> int:
        """Find the represented-tree root without changing it.

        Args:
            vertex: Vertex in the requested component.

        Returns:
            Represented root vertex index.

        Raises:
            IndexError: If vertex is outside ``[0, n)``.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        self._access(vertex)
        while True:
            self._push(vertex)
            left = self._left[vertex]
            if left == -1:
                break
            vertex = left
        self._splay(vertex)
        return vertex

    def parent(self, vertex: int) -> int:
        """Find the represented parent while preserving the root.

        Args:
            vertex: Vertex whose parent is requested.

        Returns:
            Parent vertex index, or -1 if vertex is a represented root.

        Raises:
            IndexError: If vertex is outside ``[0, n)``.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        self._access(vertex)
        vertex = self._left[vertex]
        if vertex == -1:
            return -1
        while True:
            self._push(vertex)
            right = self._right[vertex]
            if right == -1:
                break
            vertex = right
        self._splay(vertex)
        return vertex

    def set(self, vertex: int, value: ValueT) -> None:
        """Replace a vertex payload while preserving the represented root.

        Args:
            vertex: Vertex to update.
            value: New payload.

        Returns:
            None.

        Raises:
            IndexError: If vertex is outside ``[0, n)``.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        self._access(vertex)
        self._values[vertex] = value
        branch = self._light[vertex]
        point = self._point_identity if branch == -1 else self._r_sum[branch]
        self._key[vertex] = self._add_vertex(point, value)
        self._pull(vertex)

    def get(self, vertex: int) -> ValueT:
        """Return a vertex payload.

        Args:
            vertex: Vertex to inspect.

        Returns:
            Current payload, without copying it.

        Raises:
            IndexError: If vertex is outside ``[0, n)``.

        Time Complexity:
            O(1).
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        return self._values[vertex]

    def tree_value(self, vertex: int) -> PathT:
        """Return the whole-tree DP after rooting at vertex.

        Args:
            vertex: Vertex to make the represented root; this change persists.

        Returns:
            Path-cluster value of the whole tree rooted at vertex. Extract the
            root answer using the field defined by the DP; other fields may
            describe the current preferred path.

        Raises:
            IndexError: If vertex is outside ``[0, n)``.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        self.reroot(vertex)
        return self._forward[vertex]

    def subtree_value(self, vertex: int, root: int | None = None) -> PathT:
        """Return the DP of a represented subtree.

        Args:
            vertex: Root of the requested subtree, included in the result.
            root: Optional represented root in the same tree. The root change
                persists; omitting it preserves the current represented root.

        Returns:
            Subtree value excluding ancestors and the incoming parent edge.

        Raises:
            IndexError: If a vertex index is outside ``[0, n)``.
            ValueError: If root and vertex are disconnected; roots are preserved.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        if root is not None:
            if not self.same(root, vertex):
                raise ValueError('root and vertex must be connected')
            self.reroot(root)
        self._access(vertex)
        # access leaves all descendants virtual and all ancestors on the left.
        return self._key[vertex]

    def path_cluster_value(self, u: int, v: int) -> PathT:
        """Return the oriented u-to-v cluster, including virtual branches.

        Args:
            u: Start vertex and new represented root; the root change persists.
            v: End vertex in the same tree.

        Returns:
            Ordered path-cluster DP with off-path branch contributions.

        Raises:
            IndexError: If either vertex is outside ``[0, n)``.
            ValueError: If u and v are disconnected; roots are preserved.

        Time Complexity:
            O(log n) amortized, assuming O(1) callbacks.
        """
        if not self.same(u, v):
            raise ValueError('path endpoints must be connected')
        self.reroot(u)
        self._access(v)
        return self._forward[v]


class _StaticTopTreeClusters(Generic[ValueT, PointT, PathT]):
    """Shared weighted cluster hierarchy for the two fixed-root interfaces."""

    def __init__(self, tree: Tree, values: Sequence[ValueT], point_identity: PointT, add_vertex: Callable[[PointT, ValueT], PathT], add_edge: Callable[[PathT], PointT], rake: Callable[[PointT, PointT], PointT], compress: Callable[[PathT, PathT], PathT]) -> None:
        if tree.root == -1:
            raise ValueError('tree must be built before constructing StaticTopTree')
        if len(values) != tree.n:
            raise ValueError('values must contain exactly tree.n elements')
        self.tree = tree
        self.n = tree.n
        self._values = list(values)
        self._point_identity = point_identity
        self._add_vertex = add_vertex
        self._add_edge = add_edge
        self._rake = rake
        self._compress = compress

        self._children: list[list[int]] = [[] for _ in range(self.n)]
        self._heavy = [-1] * self.n
        for vertex_id in range(self.n):
            heavy = -1
            best_size = -1
            for child, _ in tree.tree[vertex_id]:
                child = int(child)
                if child == int(tree.par_v[vertex_id]):
                    continue
                self._children[vertex_id].append(child)
                child_size = tree.size[child]
                if child_size > best_size:
                    best_size = child_size
                    heavy = child
            self._heavy[vertex_id] = heavy
            if heavy != -1 and self._children[vertex_id][0] != heavy:
                heavy_index = self._children[vertex_id].index(heavy)
                self._children[vertex_id][0], self._children[vertex_id][heavy_index] = (
                    self._children[vertex_id][heavy_index],
                    self._children[vertex_id][0],
                )

        self._parent = [-1] * self.n
        self._left = [-1] * self.n
        self._right = [-1] * self.n
        self._is_compress = [False] * self.n
        self._path_values = [add_vertex(point_identity, values[0])] * self.n
        self._point_values = [point_identity] * self.n

        self._root = self._build_compress(int(tree.root))

        order: list[int] = []
        stack = [self._root]
        while stack:
            node = stack.pop()
            order.append(node)
            left = self._left[node]
            right = self._right[node]
            if left != -1:
                stack.append(left)
            if right != -1:
                stack.append(right)
        for node in reversed(order):
            self._pull(node)

    def _new_node(self, left: int, right: int, is_compress: bool) -> int:
        node = len(self._left)
        self._is_compress.append(is_compress)
        self._left.append(left)
        self._right.append(right)
        self._parent.append(-1)
        self._path_values.append(self._path_values[0])
        self._point_values.append(self._point_identity)
        if left != -1:
            self._parent[left] = node
        if right != -1:
            self._parent[right] = node
        return node

    def _merge_nodes(self, nodes: list[int], weights: list[int], is_compress: bool) -> int:
        if len(nodes) == 1:
            return nodes[0]
        # Build the binary radix tree of doubled weighted midpoints in O(k).
        # Adjacent midpoint XORs give split levels; a monotone stack merges
        # lower levels first while preserving the input order. A weight-w
        # leaf has depth O(1 + log(W / w)), where W is the total weight.
        stack = [nodes[0]]
        levels: list[int] = []
        total = weights[0]
        previous = total
        for index in range(1, len(nodes)):
            weight = weights[index]
            midpoint = (total << 1) + weight
            level = (previous ^ midpoint).bit_length()
            while levels and levels[-1] < level:
                levels.pop()
                right = stack.pop()
                stack[-1] = self._new_node(stack[-1], right, is_compress)
            levels.append(level)
            stack.append(nodes[index])
            total += weight
            previous = midpoint
        while levels:
            levels.pop()
            right = stack.pop()
            stack[-1] = self._new_node(stack[-1], right, is_compress)
        return stack[0]

    def _build_add_vertex(self, vertex_id: int) -> int:
        rake_node = self._build_rake(vertex_id)
        self._left[vertex_id] = rake_node
        self._right[vertex_id] = -1
        if rake_node != -1:
            self._parent[rake_node] = vertex_id
        return vertex_id

    def _build_add_edge(self, vertex_id: int) -> int:
        return self._new_node(self._build_compress(vertex_id), -1, False)

    def _build_rake(self, vertex_id: int) -> int:
        if len(self._children[vertex_id]) <= 1:
            return -1
        nodes = [self._build_add_edge(child) for child in self._children[vertex_id][1:]]
        weights = [self.tree.size[child] for child in self._children[vertex_id][1:]]
        return self._merge_nodes(nodes, weights, False)

    def _build_compress(self, vertex_id: int) -> int:
        nodes: list[int] = []
        weights: list[int] = []
        current = vertex_id
        while current != -1:
            nodes.append(self._build_add_vertex(current))
            heavy = self._heavy[current]
            weights.append(self.tree.size[current] - (self.tree.size[heavy] if heavy != -1 else 0))
            current = heavy
        return self._merge_nodes(nodes, weights, True)

    def _pull(self, node: int) -> None:
        left = self._left[node]
        right = self._right[node]
        # Original vertices occupy [0, n); other unary nodes convert paths
        # to points. Only binary nodes need a rake/compress discriminator.
        if node < self.n:
            point = self._point_identity if left == -1 else self._point_values[left]
            self._path_values[node] = self._add_vertex(point, self._values[node])
        elif right == -1:
            self._point_values[node] = self._add_edge(self._path_values[left])
        elif self._is_compress[node]:
            self._path_values[node] = self._compress(self._path_values[left], self._path_values[right])
        else:
            self._point_values[node] = self._rake(self._point_values[left], self._point_values[right])

    def _set(self, vertex: int, value: ValueT) -> None:
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        self._values[vertex] = value
        while vertex != -1:
            self._pull(vertex)
            vertex = self._parent[vertex]

    def _subtree_value(self, vertex: int, result: PathT) -> PathT:
        # Append the heavy descendants without including the incoming edge.
        while self._parent[vertex] != -1 and self._is_compress[self._parent[vertex]]:
            parent = self._parent[vertex]
            if self._left[parent] == vertex:
                result = self._compress(result, self._path_values[self._right[parent]])
            vertex = parent
        return result


class StaticTopTree(_StaticTopTreeClusters[ValueT, PointT, PathT]):
    """Maintain tree DP under vertex updates on a fixed rooted tree.

    The callbacks match :class:`TopTree`: ``add_vertex(point, value)`` builds
    a vertex cluster, ``add_edge(path)`` converts a child path to a point,
    ``rake`` merges points, and ``compress`` concatenates paths from parent
    to child. ``point_identity`` is the identity of ``rake``. Callbacks must
    not mutate their arguments.

    Unlike the dynamic version, the root and preferred paths stay fixed.
    Rake merges preserve the order of light children after moving a largest
    child to the front, so rake need not be commutative. For interchangeable
    static/dynamic DP callbacks, use a commutative rake and definitions whose
    answers are independent of preferred-path decomposition.

    Clusters are balanced by subtree weight. Each vertex has O(log n)
    cluster ancestors, including on trees with nested long heavy paths.
    The supplied Tree must not be rebuilt or modified after construction.
    Edge payloads are supported by :class:`StaticTopTreeWithEdges`.

    Space Complexity:
        O(n), assuming O(1)-size values and aggregates.

    Examples:
        >>> from cplib.graph.base import Node
        >>> from operator import add
        >>> graph = Tree(2)
        >>> graph.add_edge(Node(0), Node(1))
        >>> graph.build(Node(0))
        >>> tree = StaticTopTree(graph, [2, 3], 0, add, lambda path: path, add, add)
        >>> tree.tree_value(), tree.subtree_value(1)
        (5, 3)
        >>> tree.set(1, 7)
        >>> tree.get(1), tree.tree_value()
        (7, 9)
    """

    def __init__(self, tree: Tree, values: Sequence[ValueT], point_identity: PointT, add_vertex: Callable[[PointT, ValueT], PathT], add_edge: Callable[[PathT], PointT], rake: Callable[[PointT, PointT], PointT], compress: Callable[[PathT, PathT], PathT]) -> None:
        """Build weighted, order-preserving rake and compress clusters.

        Args:
            tree: Built rooted tree; its topology and root remain fixed.
            values: One initial payload per vertex.
            point_identity: Identity of rake for an empty set of branches.
            add_vertex: Callback ``(point, value) -> path``.
            add_edge: Callback ``path -> point``.
            rake: Associative point merge with point_identity as identity.
            compress: Associative ordered path merge.

        Returns:
            None.

        Raises:
            ValueError: If tree is unbuilt or the payload count is invalid.

        Time Complexity:
            O(n), assuming O(1) callbacks.
        """
        super().__init__(tree, values, point_identity, add_vertex, add_edge, rake, compress)

    def set(self, vertex: int, value: ValueT) -> None:
        """Replace a vertex payload and refresh its cluster ancestors.

        Args:
            vertex: Vertex to update.
            value: New payload.

        Returns:
            None.

        Raises:
            IndexError: If vertex is outside [0, n).

        Time Complexity:
            O(log n), assuming O(1) callbacks.
        """
        self._set(vertex, value)

    def get(self, vertex: int) -> ValueT:
        """Return a vertex payload without copying it.

        Args:
            vertex: Vertex to inspect.

        Returns:
            Current payload.

        Raises:
            IndexError: If vertex is outside [0, n).

        Time Complexity:
            O(1).
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        return self._values[vertex]

    def tree_value(self) -> PathT:
        """Return the fixed-root whole-tree cluster value.

        Returns:
            Path cluster of the whole tree; the answer field is DP-specific.

        Time Complexity:
            O(1).
        """
        return self._path_values[self._root]

    def subtree_value(self, vertex: int) -> PathT:
        """Return a fixed-root subtree's cluster value.

        Args:
            vertex: Root of the requested subtree, included in the result.

        Returns:
            Subtree cluster, excluding ancestors and the incoming parent edge.

        Raises:
            IndexError: If vertex is outside [0, n).

        Time Complexity:
            O(log n), assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        return self._subtree_value(vertex, self._path_values[vertex])


class StaticTopTreeWithEdges(_StaticTopTreeClusters[int, PointT, PathT], Generic[VertexValueT, EdgeValueT, PointT, PathT]):
    """Manage fixed-root tree DP with separate vertex and edge payloads.

    Callbacks match TopTreeWithEdges. An edge is conceptually an additional
    vertex between its endpoints. Since the root is fixed, its branch-free
    cluster can be compressed directly with the child vertex cluster: no
    expanded Tree or additional cluster hierarchy is allocated.

    The edge callback receives point_identity in this implementation; the
    dynamic version can also give it virtual branches after a path changes.
    Both definitions must describe the same DP under either decomposition.
    Callbacks must not mutate their arguments. Rake preserves light-child
    order as in StaticTopTree; use commutative rake for dynamic compatibility.
    Do not rebuild or modify the supplied Tree after construction.

    Space Complexity:
        O(n), assuming O(1)-size payloads and aggregates.
    """

    def __init__(self, tree: Tree, vertex_values: Sequence[VertexValueT], edge_values: Sequence[EdgeValueT], point_identity: PointT, vertex_cluster: Callable[[PointT, VertexValueT], PathT], edge_cluster: Callable[[PointT, EdgeValueT], PathT], add_edge: Callable[[PathT], PointT], rake: Callable[[PointT, PointT], PointT], compress: Callable[[PathT, PathT], PathT]) -> None:
        """Construct tree DP with distinct vertex and edge value types.

        Args:
            tree: Built rooted tree whose topology and root stay fixed.
            vertex_values: Initial payloads for vertices [0, n).
            edge_values: Initial payloads in tree edge-ID order.
            point_identity: Identity of rake for an empty set of branches.
            vertex_cluster: Callback (point, vertex_value) -> path.
            edge_cluster: Callback (point, edge_value) -> path for an edge node.
            add_edge: Callback converting a path to a point contribution.
            rake: Associative point merge; must be commutative for dynamic DP.
            compress: Associative ordered path merge.

        Returns:
            None.

        Raises:
            ValueError: If tree is unbuilt or a payload count is invalid.

        Time Complexity:
            O(n), assuming O(1) callbacks.
        """
        if tree.root == -1:
            raise ValueError('tree must be built before constructing StaticTopTreeWithEdges')
        if len(vertex_values) != tree.n or len(edge_values) != tree.m:
            raise ValueError('payload counts must match the vertices and edges')
        self.n = tree.n
        self.m = tree.m
        self._vertex_values = vertices = list(vertex_values)
        self._edge_values = payloads = list(edge_values)
        self._vertex_cluster = vertex_cluster
        incoming = [int(edge_id) for edge_id in tree.par_e]
        self._edge_child = [int(child) for _, child in tree.edges]

        def cluster(point: PointT, vertex: int) -> PathT:
            path = vertex_cluster(point, vertices[vertex])
            edge_id = incoming[vertex]
            if edge_id == -1:
                return path
            return compress(edge_cluster(point_identity, payloads[edge_id]), path)

        super().__init__(tree, range(tree.n), point_identity, cluster, add_edge, rake, compress)

    def set_vertex(self, vertex: int, value: VertexValueT) -> None:
        """Replace a vertex payload without changing topology or roots.

        Args:
            vertex: Original vertex index.
            value: New payload.

        Returns:
            None.

        Raises:
            IndexError: If vertex is outside [0, n).

        Time Complexity:
            O(log n), assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        self._vertex_values[vertex] = value
        self._set(vertex, vertex)

    def get_vertex(self, vertex: int) -> VertexValueT:
        """Return a vertex payload without copying it.

        Args:
            vertex: Original vertex index.

        Returns:
            Current payload.

        Raises:
            IndexError: If vertex is outside [0, n).

        Time Complexity:
            O(1).
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        return self._vertex_values[vertex]

    def set_edge(self, edge_id: int, value: EdgeValueT) -> None:
        """Replace an edge payload without changing topology or roots.

        Args:
            edge_id: Edge slot index.
            value: New payload.

        Returns:
            None.

        Raises:
            IndexError: If edge_id is outside [0, m).

        Time Complexity:
            O(log n), assuming O(1) callbacks.
        """
        if not 0 <= edge_id < self.m:
            raise IndexError('edge index out of range')
        self._edge_values[edge_id] = value
        node = self._edge_child[edge_id]
        self._set(node, node)

    def get_edge(self, edge_id: int) -> EdgeValueT:
        """Return an edge payload without copying it.

        Args:
            edge_id: Edge slot index.

        Returns:
            Current payload.

        Raises:
            IndexError: If edge_id is outside [0, m).

        Time Complexity:
            O(1).
        """
        if not 0 <= edge_id < self.m:
            raise IndexError('edge index out of range')
        return self._edge_values[edge_id]

    def tree_value(self) -> PathT:
        """Return the DP cluster of the whole fixed-root tree.

        Returns:
            Whole-tree path cluster; extract the answer field defined by the DP.

        Time Complexity:
            O(1).
        """
        return self._path_values[self._root]

    def subtree_value(self, vertex: int) -> PathT:
        """Return a subtree cluster excluding its incoming parent edge.

        Args:
            vertex: Original vertex at the root of the requested subtree.

        Returns:
            Fixed-root subtree cluster containing its vertices and internal edges.

        Raises:
            IndexError: If vertex is outside [0, n).

        Time Complexity:
            O(log n), assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        left = self._left[vertex]
        point = self._point_identity if left == -1 else self._point_values[left]
        path = self._vertex_cluster(point, self._vertex_values[vertex])
        return self._subtree_value(vertex, path)


class TopTreeWithEdges(Generic[VertexValueT, EdgeValueT, PointT, PathT]):
    """Manage dynamic tree DP with separate vertex and edge payloads.

    Each edge is represented by an internal vertex. Vertex and edge callbacks
    must construct reversal-invariant one-node clusters compatible with the
    same add_edge, rake, and compress operations as TopTree. In particular,
    rake is a commutative monoid, with no inverse required. Callbacks must not
    mutate their arguments. A physical edge is undirected: edge_cluster must
    describe the same operation viewed from either endpoint.

    Edge IDs are fixed slots in input order. cut_edge detaches a slot and
    link_edge reuses it, retaining its payload. Public vertex indices always
    refer to original vertices, never internal edge nodes. Failed topology
    operations preserve roots, topology, and payloads.

    Space Complexity:
        O(n + m), for n original vertices and m edge slots, with O(1) payloads.

    Examples:
        >>> from operator import add
        >>> tree = TopTreeWithEdges([2, 3], [(0, 1)], [10], 0,
        ...                         add, add, lambda path: path, add, add)
        >>> tree.tree_value(0), tree.subtree_value(1)
        (15, 3)
        >>> tree.cut_edge(0)
        >>> tree.set_edge(0, 20)
        >>> tree.get_edge(0), tree.same(0, 1)
        (20, False)
        >>> tree.link_edge(0, child=1, parent=0)
        >>> tree.tree_value(0)
        25
    """

    def __init__(self, vertex_values: Sequence[VertexValueT], edges: Sequence[tuple[int, int]], edge_values: Sequence[EdgeValueT], point_identity: PointT, vertex_cluster: Callable[[PointT, VertexValueT], PathT], edge_cluster: Callable[[PointT, EdgeValueT], PathT], add_edge: Callable[[PathT], PointT], rake: Callable[[PointT, PointT], PointT], compress: Callable[[PathT, PathT], PathT]) -> None:
        """Construct tree DP with distinct vertex and edge value types.

        Args:
            vertex_values: Initial payloads for vertices [0, n).
            edges: Initial undirected forest edges in edge-ID order. Each (u, v)
                links u's component below v's in input order, preserving v's root.
            edge_values: One initial payload per edge slot.
            point_identity: Identity of rake for an empty set of branches.
            vertex_cluster: Callback (point, vertex_value) -> path.
            edge_cluster: Callback (point, edge_value) -> path for an edge node.
            add_edge: Callback converting a path to a point contribution.
            rake: Associative point merge; must be commutative for dynamic DP.
            compress: Associative ordered path merge.

        Returns:
            None.

        Raises:
            IndexError: If an endpoint is outside [0, n).
            ValueError: If edge counts differ or the edges contain a cycle.

        Time Complexity:
            O(n + m log(n + m)), assuming O(1) callbacks.
        """
        self.n = n = len(vertex_values)
        self.m = len(edges)
        if len(edge_values) != self.m:
            raise ValueError('edge_values must contain one payload per edge')
        if any(not (0 <= u < n and 0 <= v < n) for u, v in edges):
            raise IndexError('vertex index out of range')
        self._vertex_values = vertices = list(vertex_values)
        self._edge_values = payloads = list(edge_values)
        self._edges = list(edges)
        self._active = [True] * self.m

        def cluster(point: PointT, node: int) -> PathT:
            if node < n:
                return vertex_cluster(point, vertices[node])
            return edge_cluster(point, payloads[node - n])

        self._tree = TopTree(range(n + self.m), point_identity, cluster, add_edge, rake, compress)
        for edge_id, (u, v) in enumerate(edges):
            self._tree.link(n + edge_id, v)
            self._tree.link(u, n + edge_id)

    def set_vertex(self, vertex: int, value: VertexValueT) -> None:
        """Replace a vertex payload without changing topology or roots.

        Args:
            vertex: Original vertex index.
            value: New payload.

        Returns:
            None.

        Raises:
            IndexError: If vertex is outside [0, n).

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        self._vertex_values[vertex] = value
        self._tree.set(vertex, vertex)

    def get_vertex(self, vertex: int) -> VertexValueT:
        """Return a vertex payload without copying it.

        Args:
            vertex: Original vertex index.

        Returns:
            Current payload.

        Raises:
            IndexError: If vertex is outside [0, n).

        Time Complexity:
            O(1).
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        return self._vertex_values[vertex]

    def set_edge(self, edge_id: int, value: EdgeValueT) -> None:
        """Replace an edge payload without changing topology or roots.

        Detached slots retain their payloads.

        Args:
            edge_id: Edge slot index.
            value: New payload.

        Returns:
            None.

        Raises:
            IndexError: If edge_id is outside [0, m).

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not 0 <= edge_id < self.m:
            raise IndexError('edge index out of range')
        self._edge_values[edge_id] = value
        node = self.n + edge_id
        self._tree.set(node, node)

    def get_edge(self, edge_id: int) -> EdgeValueT:
        """Return an edge payload without copying it. Detached slots retain their payloads.

        Args:
            edge_id: Edge slot index.

        Returns:
            Current payload.

        Raises:
            IndexError: If edge_id is outside [0, m).

        Time Complexity:
            O(1).
        """
        if not 0 <= edge_id < self.m:
            raise IndexError('edge index out of range')
        return self._edge_values[edge_id]

    def cut_edge(self, edge_id: int) -> None:
        """Detach an edge slot and root its components at its stored endpoints.

        The slot and its payload remain available for link_edge. After cutting
        the stored (u, v) edge, the two component roots are u and v.

        Args:
            edge_id: Active edge slot to detach.

        Returns:
            None.

        Raises:
            IndexError: If edge_id is outside [0, m).
            ValueError: If the slot is already detached.

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not 0 <= edge_id < self.m:
            raise IndexError('edge index out of range')
        if not self._active[edge_id]:
            raise ValueError('edge slot is already detached')
        u, v = self._edges[edge_id]
        tree = self._tree
        tree.reroot(u)
        tree.cut_parent(self.n + edge_id)
        tree.cut_parent(v)
        self._active[edge_id] = False

    def link_edge(self, edge_id: int, child: int, parent: int) -> None:
        """Reuse a detached edge slot to connect two components.

        Reroot the child's component at child, attach it below parent, and
        preserve the parent's previous represented root. The stored endpoints
        become (child, parent). The existing edge payload is retained.

        Args:
            edge_id: Detached edge slot to reuse.
            child: Endpoint in the component to reroot.
            parent: Endpoint in the component whose root is preserved.

        Returns:
            None.

        Raises:
            IndexError: If an edge or vertex index is outside its valid range.
            ValueError: If the slot is active or the endpoints are connected.

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not 0 <= edge_id < self.m:
            raise IndexError('edge index out of range')
        if not (0 <= child < self.n and 0 <= parent < self.n):
            raise IndexError('vertex index out of range')
        if self._active[edge_id]:
            raise ValueError('edge slot is already connected')
        if self._tree.same(child, parent):
            raise ValueError('link requires different components')
        self._tree.link(self.n + edge_id, parent)
        self._tree.link(child, self.n + edge_id)
        self._edges[edge_id] = child, parent
        self._active[edge_id] = True

    def same(self, u: int, v: int) -> bool:
        """Test whether two original vertices are connected.

        Args:
            u: First original vertex.
            v: Second original vertex.

        Returns:
            Whether u and v belong to the same tree.

        Raises:
            IndexError: If an original vertex index is outside [0, n).

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        return self._tree.same(u, v)

    def root(self, vertex: int) -> int:
        """Return the represented root without changing it.

        Args:
            vertex: Original vertex to inspect.

        Returns:
            Original vertex index of the component root.

        Raises:
            IndexError: If an original vertex index is outside [0, n).

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        return self._tree.root(vertex)

    def parent(self, vertex: int) -> int:
        """Return the represented parent, skipping the internal edge node.

        Args:
            vertex: Original vertex to inspect.

        Returns:
            Original parent vertex, or -1 at a component root.

        Raises:
            IndexError: If an original vertex index is outside [0, n).

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        edge = self._tree.parent(vertex)
        return -1 if edge == -1 else self._tree.parent(edge)

    def reroot(self, vertex: int) -> None:
        """Make an original vertex the represented root.

        Args:
            vertex: New root; the change persists.

        Returns:
            None.

        Raises:
            IndexError: If an original vertex index is outside [0, n).

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        self._tree.reroot(vertex)

    def tree_value(self, vertex: int) -> PathT:
        """Return the whole-tree DP after rooting at vertex.

        Args:
            vertex: New root; the change persists.

        Returns:
            Whole-tree cluster, including all connected vertex and edge payloads.
            The answer field is DP-specific; other fields may describe a path.

        Raises:
            IndexError: If an original vertex index is outside [0, n).

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not 0 <= vertex < self.n:
            raise IndexError('vertex index out of range')
        return self._tree.tree_value(vertex)

    def subtree_value(self, vertex: int, root: int | None = None) -> PathT:
        """Return a subtree DP, excluding the incoming parent edge.

        Args:
            vertex: Original vertex at the root of the requested subtree.
            root: Optional represented root; a successful change persists.

        Returns:
            Cluster containing subtree vertices and internal edges.

        Raises:
            IndexError: If an original vertex index is outside [0, n).
            ValueError: If root and vertex are disconnected; roots are preserved.

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not (0 <= vertex < self.n and (root is None or 0 <= root < self.n)):
            raise IndexError('vertex index out of range')
        return self._tree.subtree_value(vertex, root)

    def path_cluster_value(self, u: int, v: int) -> PathT:
        """Return the oriented u-to-v cluster with off-path branches.

        Args:
            u: Path start and new root; the change persists.
            v: Path end in the same tree.

        Returns:
            Ordered path cluster containing vertex, edge, and branch contributions.

        Raises:
            IndexError: If an original vertex index is outside [0, n).
            ValueError: If u and v are disconnected; roots are preserved.

        Time Complexity:
            O(log(n + m)) amortized, assuming O(1) callbacks.
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex index out of range')
        return self._tree.path_cluster_value(u, v)
