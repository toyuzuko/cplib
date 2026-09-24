"""All-roots tree DP and fixed-topology DP with vertex and edge updates."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Generic, TypeVar

from cplib.datastructure.segtree import SegmentTree
from cplib.graph.base import EdgeNum, Node
from cplib.graph.core import Tree
from cplib.graph.treedecomp import HeavyLightDecomposition
from cplib.tools.type import ValueT, VertexValueT, EdgeValueT

__all__ = ['rerooting_dp', 'FixedRootTreeDP']


TransformT = TypeVar('TransformT')


def rerooting_dp(tree: Tree, ie: ValueT, merge: Callable[[ValueT, ValueT], ValueT], put_edge: Callable[[ValueT, EdgeNum], ValueT], put_vertex: Callable[[ValueT, Node], ValueT]) -> list[ValueT]:
    """Compute all-roots DP values with the rerooting technique.

    Args:
        tree: Built rooted tree on which to run rerooting.
        ie: Identity element for ``merge``.
        merge: Associative operation on neighbor contributions, folded in
            adjacency-list order. Commutativity is not required.
        put_edge: Maps one child DP value across an incident edge.
        put_vertex: Finalizes the merged contribution at one vertex.

    Returns:
        list[ValueT]: DP answer when each vertex is treated as the root,
        independent of the root used to build ``tree``.

    Notes:
        Callbacks must not mutate their arguments; identity and intermediate
        values may be shared between vertices.

    Raises:
        ValueError: If ``tree`` has not been built yet.

    Time Complexity:
        - ``O(n)``, assuming each callback runs in ``O(1)``

    Space Complexity:
        - ``O(n)``

    Complexity Notation:
        ``n`` is the number of vertices.

    Examples:
        >>> tree = Tree(3)
        >>> tree.add_edge(0, 1)
        >>> tree.add_edge(1, 2)
        >>> tree.build(0)
        >>> rerooting_dp(tree, 0, max, lambda value, _edge: value + 1, lambda value, _vertex: value)
        [2, 1, 2]
    """
    if tree.root == -1:
        raise ValueError('This tree has not been built yet')
    down = [ie] * tree.n
    up = [ie] * tree.n
    res = [ie] * tree.n
    for v in reversed(tree.ord):
        val = ie
        for a, e in tree.tree[v]:
            if tree.par_v[v] != a:
                val = merge(val, put_edge(down[a], e))
        down[v] = put_vertex(val, v)
    for v in tree.ord:
        contributions: list[ValueT] = []
        prefix = [ie]
        for a, e in tree.tree[v]:
            contribution = up[v] if a == tree.par_v[v] else put_edge(down[a], e)
            contributions.append(contribution)
            prefix.append(merge(prefix[-1], contribution))
        res[v] = put_vertex(prefix[-1], v)
        suffix = ie
        for i in range(len(contributions) - 1, -1, -1):
            a, e = tree.tree[v][i]
            if a != tree.par_v[v]:
                up[a] = put_edge(put_vertex(merge(prefix[i], suffix), v), e)
            suffix = merge(contributions[i], suffix)
    return res


class FixedRootTreeDP(Generic[VertexValueT, EdgeValueT, ValueT, TransformT]):
    """
    Maintain a DP under vertex and edge updates on a fixed rooted tree.

    The tree topology and represented root are fixed after construction.
    ``merge`` must form a commutative group with ``value_identity`` and ``inv``;
    updates remove old contributions without preserving their positions.

    This structure is for tree DP problems where each vertex combines:

    1. its own vertex payload,
    2. the contributions of all light children merged into one value, and
    3. the contribution coming from the heavy child chain, represented as a transform.

    The DP state of one subtree is represented by ``ValueT``. Each vertex stores a
    transform ``TransformT`` that says how the heavy-child contribution should be folded
    together with the vertex payload and the already-merged light-child value.
    Heavy-light decomposition is then used to compose those transforms along a
    chain, so point updates on vertices or edges can refresh the whole rooted DP.

    The expected interpretation of the callbacks is:

    - ``put_vertex(vertex_value, vertex) -> ValueT``:
      converts the local value of one vertex into the base DP value at that vertex.
    - ``put_edge(child_value, edge_value, edge_id) -> ValueT``:
      converts a child subtree value into the contribution seen from its parent.
    - ``merge(left, right) -> ValueT``:
      combines contributions with a commutative group operation.
    - ``inv(value) -> ValueT``:
      removes an old contribution from a merged value.
    - ``make_transform(...) -> TransformT``:
      builds the heavy-path transition stored at one vertex.
    - ``compose`` and ``apply``:
      combine and evaluate heavy-path transitions.

    Typical use cases include fixed-root path-composite sums, affine DP on
    rooted trees, and any setting where one child can be treated specially and
    the remaining children can be merged independently.

    Space Complexity:
        - ``O(n)``

    Complexity Notation:
        ``n`` is the number of vertices. Each callback is assumed to run in
        ``O(1)``.
    """

    def __init__(self, tree: Tree,
                 vertex_values: Sequence[VertexValueT],
                 edge_values: Sequence[EdgeValueT],
                 value_identity: ValueT,
                 merge: Callable[[ValueT, ValueT], ValueT],
                 inv: Callable[[ValueT], ValueT],
                 put_vertex: Callable[[VertexValueT, Node], ValueT],
                 put_edge: Callable[[ValueT, EdgeValueT, EdgeNum], ValueT],
                 transform_identity: TransformT,
                 compose: Callable[[TransformT, TransformT], TransformT],
                 apply: Callable[[TransformT, ValueT], ValueT],
                 make_transform: Callable[[VertexValueT, ValueT, Node, EdgeValueT | None, EdgeNum | None], TransformT]) -> None:
        """Preprocess one rooted tree for dynamic fixed-root DP queries.

        Args:
            tree: Built rooted tree. The root of ``tree`` is the fixed root of
                the maintained DP.
            vertex_values: Initial payload for each vertex in vertex index order.
            edge_values: Initial payload for each edge in edge index order.
            value_identity: Identity element of ``merge``.
            merge: Binary operation used to combine child contributions of type
                ``ValueT``. Must be associative and commutative, with identity
                ``value_identity`` and inverse ``inv``.
            inv: Inverse operation for ``merge`` used when one old contribution
                must be removed from an already-merged light-child aggregate.
            put_vertex: Converts one vertex payload into the base DP value of
                that vertex before child contributions are added.
            put_edge: Converts a child subtree value into the contribution that
                enters the parent through one edge.
            transform_identity: Identity element of ``compose``.
            compose: Composition operation on heavy-path transforms.
            apply: Evaluates a composed heavy-path transform on an ``ValueT`` value.
            make_transform: Builds the transform stored at one vertex. Its
                arguments are:
                1. the payload of the vertex itself,
                2. the vertex base from ``put_vertex`` merged with the
                   contributions of all light children,
                3. the vertex index,
                4. the payload of the heavy edge, or ``None`` if there is no
                   heavy child,
                5. the heavy edge index, or ``None`` if there is no heavy child.
                Applying the transform to a heavy-child DP value must merge
                its ``put_edge`` contribution with argument 2. With no heavy
                child, applying it to ``value_identity`` must yield argument 2.

        Raises:
            ValueError: If ``tree`` has not been built yet.
            ValueError: If ``vertex_values`` or ``edge_values`` has a wrong length.

        Returns:
            ``None``.

        Time Complexity:
            O(n log n)
        """
        if tree.root == -1:
            raise ValueError('tree must be built before constructing FixedRootTreeDP')
        if len(vertex_values) != tree.n:
            raise ValueError('vertex_values must contain exactly tree.n elements')
        if len(edge_values) != tree.m:
            raise ValueError('edge_values must contain exactly tree.m elements')

        self.tree = tree
        self.n = tree.n
        self.value_identity = value_identity
        self.merge = merge
        self.inv = inv
        self.put_vertex = put_vertex
        self.put_edge = put_edge
        self.transform_identity = transform_identity
        self.compose = compose
        self.apply = apply
        self.make_transform = make_transform

        self.vertex_values = list(vertex_values)
        self.edge_values = list(edge_values)

        self.hld = HeavyLightDecomposition(tree)
        self.parent = [int(v) for v in tree.par_v]
        self.parent_edge = [int(e) for e in tree.par_e]
        self.heavy = [int(v) for v in self.hld.nxt]
        self.top = [int(v) for v in self.hld.top]
        self.position = self.hld.id[:]

        self.edge_child = [0] * tree.m
        self.edge_to_child = [-1] * self.n
        for edge_id in range(tree.m):
            _, child = tree.edges[edge_id]
            child = int(child)
            self.edge_child[edge_id] = child
            self.edge_to_child[child] = edge_id

        self.vertex_base = [self.value_identity] * self.n
        self.light_value = [self.value_identity] * self.n
        self.chain_end = [0] * self.n
        self.chain_value = [self.value_identity] * self.n

        for vertex in range(self.n):
            self.vertex_base[vertex] = self.put_vertex(self.vertex_values[vertex], Node(vertex))
            self.light_value[vertex] = self.vertex_base[vertex]
            head = self.top[vertex]
            self.chain_end[head] = max(self.chain_end[head], self.position[vertex] + 1)

        self.subtree_value_cache = [self.value_identity] * self.n
        for vertex in tree.ord[::-1]:
            value = self.vertex_base[vertex]
            for child, edge_id in tree.tree[vertex]:
                child = int(child)
                if child == self.parent[vertex]:
                    continue
                child_value = self.put_edge(self.subtree_value_cache[child], self.edge_values[int(edge_id)], edge_id)
                value = self.merge(value, child_value)
                if child != self.heavy[vertex]:
                    self.light_value[vertex] = self.merge(self.light_value[vertex], child_value)
            self.subtree_value_cache[vertex] = value

        base = [self.transform_identity] * self.n
        for vertex in range(self.n):
            base[self.position[vertex]] = self._build_transform(vertex)

        self.seg = SegmentTree[TransformT](self.n, self.compose, self.transform_identity)
        self.seg.build(base)

        for vertex in range(self.n):
            if self.top[vertex] == vertex:
                self.chain_value[vertex] = self._chain_value(vertex)

    def _build_transform(self, vertex: int) -> TransformT:
        heavy = self.heavy[vertex]
        if heavy == -1:
            return self.make_transform(self.vertex_values[vertex], self.light_value[vertex], Node(vertex), None, None)
        edge_id = self.edge_to_child[heavy]
        return self.make_transform(
            self.vertex_values[vertex],
            self.light_value[vertex],
            Node(vertex),
            self.edge_values[edge_id],
            EdgeNum(edge_id),
        )

    def _rebuild_vertex(self, vertex: int) -> None:
        self.seg.set(self.position[vertex], self._build_transform(vertex))

    def _chain_value(self, head: int) -> ValueT:
        return self.apply(self.seg.prod(self.position[head], self.chain_end[head]), self.value_identity)

    def _propagate(self, vertex: int) -> None:
        head = self.top[vertex]
        while True:
            new_value = self._chain_value(head)
            old_value = self.chain_value[head]
            if new_value == old_value:
                return
            self.chain_value[head] = new_value
            if head == int(self.tree.root):
                return
            parent = self.parent[head]
            edge_id = self.parent_edge[head]
            old_contribution = self.put_edge(old_value, self.edge_values[edge_id], EdgeNum(edge_id))
            new_contribution = self.put_edge(new_value, self.edge_values[edge_id], EdgeNum(edge_id))
            self.light_value[parent] = self.merge(
                self.merge(self.light_value[parent], self.inv(old_contribution)),
                new_contribution,
            )
            self._rebuild_vertex(parent)
            head = self.top[parent]

    def set_vertex(self, vertex: int, value: VertexValueT) -> None:
        """
        Overwrite one vertex payload and refresh dependent DP values.

        Args:
            vertex: Vertex to update.
            value: New payload stored at that vertex.

        Returns:
            ``None``.

        Time Complexity:
            O(log^2 n)
        """
        old_base = self.vertex_base[vertex]
        self.vertex_values[vertex] = value
        new_base = self.put_vertex(value, Node(vertex))
        self.vertex_base[vertex] = new_base
        self.light_value[vertex] = self.merge(self.merge(self.light_value[vertex], self.inv(old_base)), new_base)
        self._rebuild_vertex(vertex)
        self._propagate(vertex)

    def get_vertex(self, vertex: int) -> VertexValueT:
        """
        Return the currently stored payload of one vertex.

        Args:
            vertex: Vertex to query.

        Returns:
            VertexValueT: Payload currently associated with ``vertex``.

        Time Complexity:
            O(1)
        """
        return self.vertex_values[vertex]

    def set_edge(self, edge_id: int, value: EdgeValueT) -> None:
        """
        Overwrite one edge payload and refresh dependent DP values.

        Args:
            edge_id: Edge to update.
            value: New payload stored on that edge.

        Returns:
            ``None``.

        Time Complexity:
            O(log^2 n)
        """
        child = self.edge_child[edge_id]
        parent = self.parent[child]
        old_value = self.edge_values[edge_id]
        self.edge_values[edge_id] = value
        if self.heavy[parent] != child:
            old_contribution = self.put_edge(self.chain_value[child], old_value, EdgeNum(edge_id))
            new_contribution = self.put_edge(self.chain_value[child], value, EdgeNum(edge_id))
            self.light_value[parent] = self.merge(
                self.merge(self.light_value[parent], self.inv(old_contribution)),
                new_contribution,
            )
        self._rebuild_vertex(parent)
        self._propagate(parent)

    def get_edge(self, edge_id: int) -> EdgeValueT:
        """
        Return the currently stored payload of one edge.

        Args:
            edge_id: Edge to query.

        Returns:
            EdgeValueT: Payload currently associated with ``edge_id``.

        Time Complexity:
            O(1)
        """
        return self.edge_values[edge_id]

    def subtree_value(self, vertex: int) -> ValueT:
        """
        Return the current DP value of the subtree rooted at ``vertex``.

        This is the subtree value under the fixed root of ``tree``. It does not
        reroot the tree at ``vertex``; it simply asks for the maintained DP
        value of the existing rooted subtree.

        Args:
            vertex: Root of the queried subtree.

        Returns:
            ValueT: DP value currently assigned to the subtree of ``vertex``.

        Time Complexity:
            O(log n)
        """
        head = self.top[vertex]
        return self.apply(self.seg.prod(self.position[vertex], self.chain_end[head]), self.value_identity)

    def tree_value(self) -> ValueT:
        """
        Return the current DP value of the whole tree.

        Returns:
            ValueT: DP value at the fixed root of ``tree``.

        Time Complexity:
            O(1)
        """
        return self.chain_value[int(self.tree.root)]
