#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Iterator, Sequence

from cplib.datastructure.dsu import DisjointSetUnion
from cplib.graph.base import Edge, EdgeNum, Node, Weight


class Graph:
    """
    Graph data structure for competitive programming.

    Supports both directed and undirected graphs with weighted edges.
    Provides efficient storage and various graph algorithms including
    shortest path, minimum spanning tree, and other graph operations.

    The graph stores edges in insertion order. For an undirected graph, each
    logical edge is stored once in ``edges`` / ``wt`` and referenced from both
    endpoints in ``graph``.

    Attributes:
        dst_inf (Weight): Integer sentinel (``2**60`` by default) for
            unreachable distances. Shortest-path algorithms require finite
            distances and intermediate finite path sums strictly between
            ``-dst_inf`` and ``dst_inf``; ``-dst_inf`` marks negative-cycle
            influence. Edge storage itself has no weight bound.
        n (int): Number of vertices in the graph.
        m (int): Number of edges in the graph.
        edges (list[Edge]): List of all edges.
        graph (list[list[tuple[Node, EdgeNum]]]]: Adjacency list representation.
        deg (list[int]): In-degree of each vertex.
        wt (list[Weight]): Weight of each edge.
        is_directed (bool): Whether the graph is directed.
        is_weighted (bool): Whether the graph has weighted edges.
        has_negative_edge (bool): Whether the graph contains negative edge weights.
        connectivity_check (bool): Whether a DSU is maintained while edges are added.
        is_connected (bool): Whether all vertices are connected when
            ``connectivity_check`` is enabled.

    Complexity Notation:
        n: Number of vertices.
        m: Number of edges.

    Space Complexity:
        - ``O(n + m)``

    Examples:
        >>> # Create an undirected graph with 4 vertices
        >>> g = Graph(4)
        >>> g.add_edge(0, 1, 5)
        >>> g.add_edge(1, 2, 3)
        >>> g.add_edge(2, 3, 2)
        >>>
        >>> # Find shortest distances from vertex 0
        >>> from cplib.graph.shortest import dijkstra
        >>> distances = dijkstra(g, 0)
        >>> distances
        [0, 5, 8, 10]

    Args:
        n: Number of vertices.
        is_directed: Whether edges are directed.
        connectivity_check: Whether to maintain weak connectivity using a DSU.
    """

    dst_inf = Weight(1 << 60)

    def __init__(self, n: int, is_directed: bool = False, connectivity_check: bool = False) -> None:
        """Initialize an empty graph with ``n`` vertices.

        Args:
            n: Number of vertices in the graph.
            is_directed: Whether the graph is directed.
            connectivity_check: Whether to maintain connectivity information
                online while edges are added.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative.

        Time Complexity:
            O(n)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.m = 0
        self.edges: list[Edge] = []
        self.graph: list[list[tuple[Node, EdgeNum]]] = [[] for _ in range(n)]
        self.deg: list[int] = [0] * n
        self.wt: list[Weight] = []
        self.is_directed = is_directed
        self.is_weighted = False
        self.has_negative_edge = False
        self.connectivity_check = connectivity_check
        if connectivity_check:
            self.dsu = DisjointSetUnion(n)
            self.is_connected = False if n > 1 else True

    def add_edge(self, u: Node, v: Node, w: Weight = Weight(1)) -> None:
        """
        Add an edge to the graph.

        Args:
            u: Source vertex (0-indexed).
            v: Target vertex (0-indexed).
            w: Weight of the edge. Defaults to Weight(1).

        Raises:
            IndexError: If u or v is out of range [0, n).

        Returns:
            ``None``.

        Notes:
            For undirected graphs, the edge is added in both directions.
            If any edge has weight != 1, the graph is marked as weighted.
            If any edge has negative weight, has_negative_edge flag is set.

        Warning:
            In undirected graphs, a negative edge creates a negative cycle
            since you can traverse the edge back and forth indefinitely.

        Time Complexity:
            O(alpha(n)) amortized with connectivity checking, otherwise O(1).
        """

        if not 0 <= u < self.n or not 0 <= v < self.n:
            raise IndexError('edge endpoint must be within [0, n)')
        self.graph[u].append((v, EdgeNum(self.m)))
        self.deg[v] += 1
        if not self.is_directed:
            self.graph[v].append((u, EdgeNum(self.m)))
            self.deg[u] += 1
        self.edges.append(Edge((u, v)))
        self.wt.append(w)
        self.m += 1
        if w != Weight(1):
            self.is_weighted = True
        if w < Weight(0):
            self.has_negative_edge = True
        if self.connectivity_check:
            if self.dsu.merge(u, v):
                self.is_connected = self.dsu.size(0) == self.n

    def adjacency_matrix(self) -> list[list[int]]:
        """
        Return the unweighted adjacency matrix of the graph.

        The returned matrix contains ``1`` if at least one edge exists from
        ``u`` to ``v`` and ``0`` otherwise. For undirected graphs, both
        directions are filled because the stored adjacency list is symmetric.

        Returns:
            ``n x n`` adjacency matrix.

        Time Complexity:
            O(n^2 + m)

        Space Complexity:
            O(n^2)
        """
        matrix = [[0] * self.n for _ in range(self.n)]
        for u, edges in enumerate(self.graph):
            row = matrix[u]
            for v, _ in edges:
                row[v] = 1
        return matrix


class CSRGraph:
    """
    Static graph representation using Compressed Sparse Row layout.

    The graph is built from a fixed edge list. After construction, outgoing
    arcs of vertex ``v`` are stored contiguously in
    ``to[start[v]:start[v + 1]]``. For undirected graphs, each logical edge is
    stored as two arcs with the same edge id.

    Attributes:
        n: Number of vertices.
        m: Number of logical edges.
        start: Offset array of length ``n + 1``.
        to: Destination vertex for each stored arc.
        edge_id: Logical edge id for each stored arc.
        weight: Weight for each stored arc.
        edges: Logical edges in input order.
        is_directed: Whether the graph is directed.
        is_weighted: Whether some edge weight is not ``1``.
        has_negative_edge: Whether some logical edge has negative weight.

    Space Complexity:
        O(n + m)
    """

    def __init__(
        self,
        n: int,
        edges: Sequence[tuple[Node, Node] | tuple[Node, Node, Weight]],
        is_directed: bool = False,
    ) -> None:
        """
        Build a CSR graph from a fixed edge list.

        Args:
            n: Number of vertices.
            edges: Logical edges. Each edge is ``(u, v)`` or ``(u, v, w)``.
            is_directed: Whether the graph is directed.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative.
            IndexError: If an edge endpoint is outside ``[0, n)``.

        Time Complexity:
            O(n + m)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.m = len(edges)
        self.is_directed = is_directed
        self.edges: list[Edge] = []
        self.edge_weight: list[Weight] = []
        self.is_weighted = False
        self.has_negative_edge = False

        degree = [0] * n
        normalized: list[tuple[int, int, Weight]] = []
        for edge in edges:
            if len(edge) == 2:
                u, v = edge
                w = Weight(1)
            else:
                u, v, w = edge
            u = int(u)
            v = int(v)
            if not 0 <= u < n or not 0 <= v < n:
                raise IndexError('edge endpoint must be within [0, n)')
            w = Weight(w)
            normalized.append((u, v, w))
            self.edges.append(Edge((Node(u), Node(v))))
            self.edge_weight.append(w)
            degree[u] += 1
            if not is_directed:
                degree[v] += 1
            if w != Weight(1):
                self.is_weighted = True
            if w < Weight(0):
                self.has_negative_edge = True

        self.start = [0] * (n + 1)
        for i in range(n):
            self.start[i + 1] = self.start[i] + degree[i]

        arc_count = self.start[n]
        self.to = [Node(0)] * arc_count
        self.edge_id = [EdgeNum(0)] * arc_count
        self.weight = [Weight(1)] * arc_count
        cursor = self.start[:]
        for i, (u, v, w) in enumerate(normalized):
            p = cursor[u]
            self.to[p] = Node(v)
            self.edge_id[p] = EdgeNum(i)
            self.weight[p] = w
            cursor[u] += 1
            if not is_directed:
                p = cursor[v]
                self.to[p] = Node(u)
                self.edge_id[p] = EdgeNum(i)
                self.weight[p] = w
                cursor[v] += 1

    @classmethod
    def from_graph(cls, graph: Graph) -> 'CSRGraph':
        """
        Build a CSR graph from an existing :class:`Graph`.

        Args:
            graph: Source graph.

        Returns:
            CSR representation with the same logical edges and weights.

        Time Complexity:
            O(n + m)
        """
        edges = [(u, v, graph.wt[i]) for i, (u, v) in enumerate(graph.edges)]
        return cls(graph.n, edges, is_directed=graph.is_directed)

    def adjacent_range(self, v: Node) -> range:
        """
        Return the arc-index range for outgoing arcs of ``v``.

        Args:
            v: Vertex.

        Returns:
            ``range(start[v], start[v + 1])``.

        Raises:
            IndexError: If ``v`` is outside ``[0, n)``.

        Time Complexity:
            O(1)
        """
        vi = int(v)
        if not 0 <= vi < self.n:
            raise IndexError('vertex must be within [0, n)')
        return range(self.start[vi], self.start[vi + 1])

    def out_degree(self, v: Node) -> int:
        """
        Return the out-degree of ``v``.

        Args:
            v: Vertex.

        Returns:
            Number of outgoing arcs from ``v``.

        Raises:
            IndexError: If ``v`` is outside ``[0, n)``.

        Time Complexity:
            O(1)
        """
        vi = int(v)
        if not 0 <= vi < self.n:
            raise IndexError('vertex must be within [0, n)')
        return self.start[vi + 1] - self.start[vi]

    def neighbors(self, v: Node) -> Iterator[Node]:
        """
        Iterate over outgoing neighbors of ``v``.

        Args:
            v: Vertex.

        Returns:
            Iterator of destination vertices.

        Time Complexity:
            O(out_degree(v))
        """
        for i in self.adjacent_range(v):
            yield self.to[i]

    def neighbor_edges(self, v: Node) -> Iterator[tuple[Node, EdgeNum]]:
        """
        Iterate over outgoing arcs of ``v`` as ``(to, edge_id)`` pairs.

        Args:
            v: Vertex.

        Returns:
            Iterator of destination vertices and logical edge ids.

        Time Complexity:
            O(out_degree(v))
        """
        for i in self.adjacent_range(v):
            yield (self.to[i], self.edge_id[i])

    def weighted_neighbor_edges(self, v: Node) -> Iterator[tuple[Node, EdgeNum, Weight]]:
        """
        Iterate over outgoing arcs of ``v`` as ``(to, edge_id, weight)``.

        Args:
            v: Vertex.

        Returns:
            Iterator of destination vertices, logical edge ids, and weights.

        Time Complexity:
            O(out_degree(v))
        """
        for i in self.adjacent_range(v):
            yield (self.to[i], self.edge_id[i], self.weight[i])


class Tree:
    """
    Rooted tree container with parent, depth, and subtree metadata.

    Add ``n - 1`` edges, then call ``build`` to orient them away from the root
    and populate traversal order, parent edges, depths, costs, and subtree sizes.

    After ``build(root)``, the following arrays become available:

    - ``par_v[v]``: parent of ``v`` or ``-1`` for the root
    - ``par_e[v]``: edge index from the parent to ``v``
    - ``dep[v]``: depth from the root measured in edges
    - ``cost[v]``: weighted distance from the root
    - ``size[v]``: size of the rooted subtree of ``v``
    - ``ord``: preorder-like traversal from the root

    Complexity Notation:
        n: Number of vertices.

    Space Complexity:
        - ``O(n)``

    Args:
        n: Number of vertices.
        connectivity_check: Whether to reject edges that close a cycle.
    """

    def __init__(self, n: int, connectivity_check: bool = False) -> None:
        """Initialize an empty tree on ``n`` vertices.

        Args:
            n: Number of vertices.
            connectivity_check: Whether to reject edges that close a cycle.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative.

        Time Complexity:
            O(n)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.m = 0
        self.tree: list[list[tuple[Node, EdgeNum]]] = [[] for _ in range(n)]
        self.edges: list[Edge] = []
        self.wt: list[Weight] = []
        self.root = Node(-1)
        self.connectivity_check = connectivity_check
        if connectivity_check:
            self.dsu = DisjointSetUnion(n)
        self.is_weighted = False

    def add_edge(self, u: Node, v: Node, w: Weight = Weight(1)) -> None:
        """
        Add one undirected edge.

        Edges rejected by the connectivity check leave the tree unchanged.

        Args:
            u: One endpoint.
            v: The other endpoint.
            w: Edge weight.

        Raises:
            IndexError: If an endpoint is outside ``[0, n)``.
            ValueError: If ``connectivity_check`` is enabled and the edge creates a cycle.

        Returns:
            ``None``.

        Time Complexity:
            O(alpha(n)) amortized with connectivity checking, otherwise O(1).
        """
        if not 0 <= u < self.n or not 0 <= v < self.n:
            raise IndexError('edge endpoint must be within [0, n)')
        if self.connectivity_check and not self.dsu.merge(u, v):
            raise ValueError(
                'Attempted to add an edge between already connected nodes')
        self.tree[u].append((v, EdgeNum(self.m)))
        self.tree[v].append((u, EdgeNum(self.m)))
        self.edges.append(Edge((u, v)))
        self.wt.append(w)
        if w != Weight(1):
            self.is_weighted = True
        self.m += 1

    def build(self, r: Node = Node(0)) -> None:
        """
        Root the tree and preprocess traversal metadata.

        Args:
            r: Root vertex.

        Raises:
            ValueError: If the graph does not contain exactly ``n - 1`` edges.
            IndexError: If ``r`` is outside ``[0, n)``.

        Returns:
            ``None``.

        Time Complexity:
            O(n)
        """
        if self.m != self.n - 1:
            raise ValueError(
                'Invalid number of edges. The number of edges must be equal to the number of nodes minus one')
        if not 0 <= r < self.n:
            raise IndexError('root must be within [0, n)')
        self.root = r
        self.par_v = [Node(-1)] * self.n
        self.par_e = [EdgeNum(-1)] * self.n
        self.dep = [0] * self.n
        self.cost = [Weight(0)] * self.n
        self.size = [1] * self.n
        self.ord: list[Node] = [r]
        stack: list[Node] = [r]
        while stack:
            v = stack.pop()
            for a, e in self.tree[v]:
                if self.par_v[v] == a:
                    continue
                self.par_v[a] = v
                self.par_e[a] = e
                self.edges[e] = Edge((v, a))
                self.dep[a] = self.dep[v] + 1
                self.cost[a] = Weight(self.cost[v] + self.wt[e])
                self.ord.append(a)
                stack.append(a)
        for v in self.ord[1:][::-1]:
            self.size[self.par_v[v]] += self.size[v]
        for e in range(self.m):
            u, v = self.edges[e]
            if self.par_v[u] == v:
                self.edges[e] = Edge((v, u))
