#!/usr/bin/env python3

"""Structured graph utilities."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Sequence
from typing import Generic

from cplib.graph.lowlink import block_cut_tree
from cplib.graph.core import Graph, Node
from cplib.graph.lowlink import analyze_lowlink
from cplib.tools.type import ValueT


class _RootedForestData:
    """Internal rooted-forest helper shared by structured graph classes."""

    def __init__(self, n: int, parent: list[int], parent_edge: list[int], depth: list[int], weighted_depth: list[int], roots: list[int]) -> None:
        self.n = n
        self.parent = parent
        self.parent_edge = parent_edge
        self.depth = depth
        self.weighted_depth = weighted_depth
        self.root = roots

        self.branch_children: list[list[int]] = [[] for _ in range(n)]
        for v in range(n):
            if parent[v] != -1:
                self.branch_children[parent[v]].append(v)

        self.branch_order: list[int] = []
        self.branch_tin = [-1] * n
        self.branch_tout = [-1] * n
        self.branch_size = [1] * n
        timer = 0
        forest_roots = [v for v in range(n) if parent[v] == -1]
        for root in forest_roots:
            stack: list[tuple[int, int]] = [(root, 0)]
            while stack:
                v, state = stack.pop()
                if state == 0:
                    self.branch_tin[v] = timer
                    self.branch_order.append(v)
                    timer += 1
                    stack.append((v, 1))
                    for u in reversed(self.branch_children[v]):
                        stack.append((u, 0))
                else:
                    size = 1
                    for u in self.branch_children[v]:
                        size += self.branch_size[u]
                    self.branch_size[v] = size
                    self.branch_tout[v] = timer

        self._log = max(1, n.bit_length())
        self._up: list[list[int]] = [parent[:]]
        for _ in range(1, self._log):
            prev = self._up[-1]
            self._up.append([-1 if p == -1 else prev[p] for p in prev])

        self.branch_heavy = [-1] * n
        for v in range(n):
            max_size = 0
            for u in self.branch_children[v]:
                if self.branch_size[u] > max_size:
                    max_size = self.branch_size[u]
                    self.branch_heavy[v] = u

        self.branch_hld_id = [-1] * n
        self.branch_hld_top = [-1] * n
        self.branch_hld_rev = [-1] * n
        timer = 0
        stack2 = list(reversed(forest_roots))
        for root in forest_roots:
            self.branch_hld_top[root] = root
        while stack2:
            v = stack2.pop()
            self.branch_hld_id[v] = timer
            self.branch_hld_rev[timer] = v
            timer += 1
            heavy = self.branch_heavy[v]
            for u in reversed(self.branch_children[v]):
                if u == heavy:
                    continue
                self.branch_hld_top[u] = u
                stack2.append(u)
            if heavy != -1:
                self.branch_hld_top[heavy] = self.branch_hld_top[v]
                stack2.append(heavy)

    def is_ancestor(self, ancestor: int, v: int) -> bool:
        if self.root[ancestor] != self.root[v]:
            return False
        return self.branch_tin[ancestor] <= self.branch_tin[v] < self.branch_tout[ancestor]

    def subtree_range(self, v: int) -> tuple[int, int]:
        return self.branch_tin[v], self.branch_tout[v]

    def path_ranges(self, u: int, v: int, edge_query: bool = False) -> list[tuple[int, int]] | None:
        if self.root[u] != self.root[v]:
            return None
        segments: list[tuple[int, int]] = []
        while True:
            if self.branch_hld_id[u] > self.branch_hld_id[v]:
                u, v = v, u
            if self.branch_hld_top[u] == self.branch_hld_top[v]:
                segments.append((self.branch_hld_id[u] + int(edge_query), self.branch_hld_id[v] + 1))
                return segments
            segments.append((self.branch_hld_id[self.branch_hld_top[v]], self.branch_hld_id[v] + 1))
            v = self.parent[self.branch_hld_top[v]]

    def lca(self, u: int, v: int) -> int | None:
        if self.root[u] != self.root[v]:
            return None
        if self.depth[u] < self.depth[v]:
            u, v = v, u
        diff = self.depth[u] - self.depth[v]
        bit = 0
        while diff:
            if diff & 1:
                u = self._up[bit][u]
            diff >>= 1
            bit += 1
        if u == v:
            return u
        for bit in range(self._log - 1, -1, -1):
            pu = self._up[bit][u]
            pv = self._up[bit][v]
            if pu != pv:
                u = pu
                v = pv
        return self.parent[u]


class _ComponentNamoriAdapter:
    """Global/local index adapter for embedding Namori inside Pseudotree."""

    def __init__(self, graph: Graph, vertices: list[int]) -> None:
        self.global_to_local = {v: i for i, v in enumerate(vertices)}
        self.local_to_global = vertices[:]
        local_graph = Graph(len(vertices))
        vertex_set = set(vertices)
        edge_ids: set[int] = set()
        for v in vertices:
            for u, e in graph.graph[v]:
                if u in vertex_set:
                    edge_ids.add(int(e))
        local_to_global_edge: list[int] = []
        for e in sorted(edge_ids):
            u, v = graph.edges[e]
            local_graph.add_edge(Node(self.global_to_local[int(u)]), Node(self.global_to_local[int(v)]), graph.wt[e])
            local_to_global_edge.append(e)
        self.namori = Namori(local_graph)
        self.cycle = [self.local_to_global[v] for v in self.namori.cycle]
        self.cycle_edges = [local_to_global_edge[e] for e in self.namori.cycle_edges]
        self.cycle_prefix_weight = self.namori.cycle_prefix_weight[:]

    def _local(self, v: int) -> int:
        return self.global_to_local[v]

    def cycle_root(self, v: int) -> int:
        return self.local_to_global[self.namori.cycle_root(self._local(v))]

    def hops_to_cycle(self, v: int) -> int:
        return self.namori.hops_to_cycle(self._local(v))

    def cycle_hops(self, u: int, v: int) -> int:
        return self.namori.cycle_hops(self._local(u), self._local(v))

    def cycle_dist(self, u: int, v: int) -> int:
        return self.namori.cycle_dist(self._local(u), self._local(v))

    def hops(self, u: int, v: int) -> int:
        return self.namori.hops(self._local(u), self._local(v))

    def dist(self, u: int, v: int) -> int:
        return self.namori.dist(self._local(u), self._local(v))

    def path_length(self, u: int, v: int) -> tuple[int, int]:
        return self.namori.path_length(self._local(u), self._local(v))

    def weighted_path_length(self, u: int, v: int) -> tuple[int, int]:
        return self.namori.weighted_path_length(self._local(u), self._local(v))


class FunctionalGraph(Generic[ValueT]):
    """
    Functional graph with cycle decomposition and optional walk aggregation.

    The graph is represented by a single outgoing edge from each vertex.
    Aggregation follows the pattern below:

    - ``start_values[v]`` is the contribution before moving from ``v``
    - ``step_values[v]`` is the contribution of taking the edge ``v -> to[v]``
    - ``op`` must be associative

    Attributes:
        to: Successor array of the functional graph.
        n: Number of vertices.

    Space Complexity:
        O(n)

    Examples:
        >>> fg = FunctionalGraph.from_vertex_values(
        ...     [1, 2, 0],
        ...     [10, 20, 30],
        ...     op=lambda a, b: a + b,
        ...     identity=0,
        ... )
        >>> fg.jump(0, 4)
        1
        >>> fg.hops_to_cycle(2)
        0
        >>> fg.prod(1, 2)
        50
    """

    def __init__(self, to: Sequence[int], start_values: Sequence[ValueT] | None = None, step_values: Sequence[ValueT] | None = None, op: Callable[[ValueT, ValueT], ValueT] | None = None) -> None:
        """
        Initialize a functional graph from its successor array.

        Args:
            to: Successor of each vertex. Every ``to[v]`` must be in ``[0, n)``.
            start_values: Optional contribution used before any movement from ``v``.
            step_values: Optional contribution of taking the edge ``v -> to[v]``.
            op: Associative operation used by ``prod``.

        Returns:
            None.

        Raises:
            ValueError: If the successor array contains an invalid vertex index.
            ValueError: If only part of the aggregation configuration is provided.
            ValueError: If a value array has a different length from ``to``.

        Time Complexity:
            O(n)

        Examples:
            >>> fg = FunctionalGraph([1, 2, 0])
            >>> fg.cycle_length(0)
            3
        """
        self.to = [int(v) for v in to]
        self.n = len(self.to)
        for v in self.to:
            if not 0 <= v < self.n:
                raise ValueError('successor indices must be within [0, n)')

        self._has_prod = start_values is not None or step_values is not None or op is not None
        if self._has_prod:
            if start_values is None or step_values is None or op is None:
                raise ValueError('start_values, step_values, and op must be provided together')
            if len(start_values) != self.n or len(step_values) != self.n:
                raise ValueError('value arrays must have the same length as to')
            self._start_values = list(start_values)
            self._step_values = list(step_values)
            self._op = op
        else:
            self._start_values = []
            self._step_values = []
            self._op = None

        self._build_structure()
        self._jump_tables: list[list[int]] = []
        self._step_tables: list[list[ValueT]] = []

    @classmethod
    def from_vertex_values(cls, to: Sequence[int], vertex_values: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT], identity: ValueT) -> FunctionalGraph[ValueT]:
        """
        Create a functional graph whose walk product uses vertex values.

        Args:
            to: Successor array of a functional graph.
            vertex_values: Values placed on vertices.
            op: Associative binary operation.
            identity: Identity element of ``op``.

        Returns:
            FunctionalGraph[ValueT]: Functional graph configured for vertex aggregation.

        Time Complexity:
            O(n)

        Examples:
            >>> fg = FunctionalGraph.from_vertex_values([1, 2, 0], [1, 2, 3], lambda a, b: a + b, 0)
            >>> fg.prod(0, 3)
            6
        """
        n = len(to)
        return cls(to=to, start_values=[identity] * n, step_values=vertex_values, op=op)

    @classmethod
    def from_edge_values(cls, to: Sequence[int], edge_values: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT], identity: ValueT) -> FunctionalGraph[ValueT]:
        """
        Create a functional graph whose walk product uses edge values.

        Args:
            to: Successor array of a functional graph.
            edge_values: Values placed on edges.
            op: Associative binary operation.
            identity: Identity element of ``op``.

        Returns:
            FunctionalGraph[ValueT]: Functional graph configured for edge aggregation.

        Time Complexity:
            O(n)

        Examples:
            >>> fg = FunctionalGraph.from_edge_values([1, 2, 0], [4, 5, 6], lambda a, b: a + b, 0)
            >>> fg.prod(0, 2)
            9
        """
        n = len(to)
        return cls(to=to, start_values=[identity] * n, step_values=edge_values, op=op)

    def _build_structure(self) -> None:
        indeg = [0] * self.n
        rev: list[list[int]] = [[] for _ in range(self.n)]
        for v, u in enumerate(self.to):
            indeg[u] += 1
            rev[u].append(v)

        removed = [False] * self.n
        q = deque(v for v in range(self.n) if indeg[v] == 0)
        while q:
            v = q.popleft()
            removed[v] = True
            u = self.to[v]
            indeg[u] -= 1
            if indeg[u] == 0:
                q.append(u)

        self._on_cycle = [not removed[v] for v in range(self.n)]
        self._cycle_id = [-1] * self.n
        self._cycle_pos = [-1] * self.n
        self._cycle_length = [0] * self.n
        self._dist_to_cycle = [-1] * self.n
        self._cycle_entry = [-1] * self.n
        self._cycles: list[list[int]] = []

        for v in range(self.n):
            if not self._on_cycle[v] or self._cycle_id[v] != -1:
                continue
            cycle: list[int] = []
            u = v
            cid = len(self._cycles)
            while self._cycle_id[u] == -1:
                self._cycle_id[u] = cid
                self._cycle_pos[u] = len(cycle)
                cycle.append(u)
                u = self.to[u]
            self._cycles.append(cycle)
            cycle_len = len(cycle)
            for node in cycle:
                self._cycle_length[node] = cycle_len
                self._dist_to_cycle[node] = 0
                self._cycle_entry[node] = node

        q = deque(v for v in range(self.n) if self._dist_to_cycle[v] == 0)
        while q:
            v = q.popleft()
            for u in rev[v]:
                if self._dist_to_cycle[u] != -1:
                    continue
                self._dist_to_cycle[u] = self._dist_to_cycle[v] + 1
                self._cycle_id[u] = self._cycle_id[v]
                self._cycle_length[u] = self._cycle_length[v]
                self._cycle_entry[u] = self._cycle_entry[v]
                q.append(u)

    def _ensure_doubling(self, k: int) -> None:
        if k <= 0:
            return
        need = k.bit_length()
        op = self._op
        if not self._jump_tables:
            self._jump_tables.append(self.to[:])
            if self._has_prod:
                self._step_tables.append(self._step_values[:])
        while len(self._jump_tables) < need:
            prev = len(self._jump_tables) - 1
            prev_jump = self._jump_tables[prev]
            self._jump_tables.append([prev_jump[prev_jump[v]] for v in range(self.n)])
            if self._has_prod:
                prev_steps = self._step_tables[prev]
                assert op is not None
                self._step_tables.append([op(prev_steps[v], prev_steps[prev_jump[v]]) for v in range(self.n)])

    def _validate_vertex(self, v: int) -> None:
        if not 0 <= v < self.n:
            raise IndexError('vertex index out of range')

    def jump(self, v: int, k: int) -> int:
        """
        Return the vertex reached after moving ``k`` steps from ``v``.

        Args:
            v: Starting vertex.
            k: Number of steps.

        Returns:
            int: Vertex reached after ``k`` transitions.

        Raises:
            IndexError: If ``v`` is out of range.
            ValueError: If ``k`` is negative.

        Time Complexity:
            O(log k), plus O(n) for each newly added doubling level.

        Examples:
            >>> fg = FunctionalGraph([1, 2, 0])
            >>> fg.jump(0, 5)
            2
        """
        self._validate_vertex(v)
        if k < 0:
            raise ValueError('k must be non-negative')
        self._ensure_doubling(k)
        bit = 0
        while k:
            if k & 1:
                v = self._jump_tables[bit][v]
            k >>= 1
            bit += 1
        return v

    def get(self, v: int, k: int) -> int:
        """
        Return the vertex reached after moving ``k`` steps from ``v``.

        Args:
            v: Starting vertex.
            k: Number of steps.

        Returns:
            int: Vertex reached after ``k`` transitions.

        Raises:
            IndexError: If ``v`` is out of range.
            ValueError: If ``k`` is negative.

        Time Complexity:
            O(log k), plus O(n) for each newly added doubling level.

        Examples:
            >>> fg = FunctionalGraph([1, 2, 0])
            >>> fg.get(1, 3)
            1
        """
        return self.jump(v, k)

    def prod(self, v: int, k: int) -> ValueT:
        """
        Return the aggregated value along the first ``k`` steps from ``v``.

        Args:
            v: Starting vertex.
            k: Number of steps.

        Returns:
            ValueT: Aggregated value on the walk prefix.

        Raises:
            ValueError: If aggregation is not configured or ``k`` is negative.
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(log k), plus O(n) for each newly added doubling level.

        Examples:
            >>> fg = FunctionalGraph.from_edge_values([1, 2, 0], [4, 5, 6], lambda a, b: a + b, 0)
            >>> fg.prod(2, 2)
            10
        """
        if not self._has_prod:
            raise ValueError('prod() is unavailable because no aggregation was configured')
        self._validate_vertex(v)
        if k < 0:
            raise ValueError('k must be non-negative')
        op = self._op
        assert op is not None
        res = self._start_values[v]
        if k == 0:
            return res
        self._ensure_doubling(k)
        bit = 0
        while k:
            if k & 1:
                res = op(res, self._step_tables[bit][v])
                v = self._jump_tables[bit][v]
            k >>= 1
            bit += 1
        return res

    def cycle_id(self, v: int) -> int:
        """
        Return the id of the cycle eventually reached from ``v``.

        Args:
            v: Query vertex.

        Returns:
            int: Zero-based id of the reachable directed cycle.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> fg = FunctionalGraph([1, 2, 0, 2])
            >>> fg.cycle_id(3)
            0
        """
        self._validate_vertex(v)
        return self._cycle_id[v]

    def cycle_length(self, v: int) -> int:
        """
        Return the length of the cycle eventually reached from ``v``.

        Args:
            v: Query vertex.

        Returns:
            int: Length of the reachable directed cycle.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> fg = FunctionalGraph([1, 2, 0, 2])
            >>> fg.cycle_length(3)
            3
        """
        self._validate_vertex(v)
        return self._cycle_length[v]

    def hops_to_cycle(self, v: int) -> int:
        """
        Return the number of steps from ``v`` to its cycle.

        Args:
            v: Query vertex.

        Returns:
            int: Distance from ``v`` to the first cycle vertex on its walk.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> fg = FunctionalGraph([1, 2, 0, 2])
            >>> fg.hops_to_cycle(3)
            1
        """
        self._validate_vertex(v)
        return self._dist_to_cycle[v]

    def is_on_cycle(self, v: int) -> bool:
        """
        Return whether ``v`` lies on a directed cycle.

        Args:
            v: Query vertex.

        Returns:
            bool: Whether ``v`` is contained in a cycle.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> fg = FunctionalGraph([1, 2, 0, 2])
            >>> fg.is_on_cycle(3)
            False
        """
        self._validate_vertex(v)
        return self._on_cycle[v]

    def cycle_entry(self, v: int) -> int:
        """
        Return the first cycle vertex reached from ``v``.

        Args:
            v: Query vertex.

        Returns:
            int: First cycle vertex on the walk from ``v``.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> fg = FunctionalGraph([1, 2, 0, 2, 3])
            >>> fg.cycle_entry(4)
            2
        """
        self._validate_vertex(v)
        return self._cycle_entry[v]


class Namori:
    """
    Connected undirected graph with exactly one simple cycle.

    The class peels leaves to recover the unique cycle and roots every attached
    tree at its incident cycle vertex.

    Attributes:
        graph: Original undirected graph.
        n: Number of vertices.
        cycle: Vertices on the unique cycle in cyclic order.
        cycle_edges: Edge ids of the unique cycle in the same order as ``cycle``.
        on_cycle: Whether each vertex belongs to the cycle.
        cycle_index: Position on ``cycle`` for cycle vertices, otherwise ``-1``.
        root: Cycle vertex to which each vertex belongs.
        depth: Number of edges from each vertex to its cycle root.
        weighted_depth: Weighted distance from each vertex to the cycle.
        parent: Parent toward the cycle, or ``-1`` for cycle vertices.
        parent_edge: Edge to the parent toward the cycle, or ``-1`` for cycle vertices.
        branches: Vertices grouped by their cycle root.
        branch_children: Children in the forest obtained by removing cycle edges.
        branch_order: Euler-tour preorder of the branch forest.
        branch_tin: Entry time of each vertex in ``branch_order``.
        branch_tout: Exit time of each vertex as a half-open interval end.
        branch_size: Size of each subtree in the branch forest.
        branch_hld_id: Position of each vertex in branch HLD order.
        branch_hld_rev: Inverse map of ``branch_hld_id``.
        branch_hld_top: Head vertex of the heavy path containing each vertex.
        branch_heavy: Heavy child of each vertex, or ``-1``.

    Space Complexity:
        O(n)

    Examples:
        >>> g = Graph(5)
        >>> g.add_edge(0, 1)
        >>> g.add_edge(1, 2)
        >>> g.add_edge(2, 0)
        >>> g.add_edge(1, 3)
        >>> g.add_edge(3, 4)
        >>> namori = Namori(g)
        >>> namori.cycle
        [0, 1, 2]
        >>> namori.cycle_root(4)
        1
    """

    def __init__(self, graph: Graph) -> None:
        """
        Build a Namori decomposition from an undirected graph.

        Args:
            graph: Connected undirected graph with ``n`` vertices and ``n`` edges.

        Returns:
            None: This constructor initializes the decomposition in place.

        Raises:
            ValueError: If the graph is directed, disconnected, or not a Namori graph.

        Time Complexity:
            O(n)

        Space Complexity:
            O(n)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(2, 3)
            >>> Namori(g).hops_to_cycle(3)
            1
        """
        if graph.is_directed:
            raise ValueError('Namori requires an undirected graph')
        if graph.m != graph.n:
            raise ValueError('Namori requires a connected graph with exactly n edges')
        if graph.n == 0:
            raise ValueError('Namori requires at least one vertex')

        self.graph = graph
        self.n = graph.n
        self._validate_connected()

        deg = [len(adj) for adj in graph.graph]
        removed = [False] * self.n
        q = deque(v for v in range(self.n) if deg[v] == 1)
        while q:
            v = q.popleft()
            if removed[v]:
                continue
            removed[v] = True
            for u, _ in graph.graph[v]:
                if removed[u]:
                    continue
                deg[u] -= 1
                if deg[u] == 1:
                    q.append(u)

        self.on_cycle = [not removed[v] for v in range(self.n)]
        if not any(self.on_cycle):
            raise ValueError('failed to extract the unique cycle')

        self.cycle, self.cycle_edges = self._build_cycle_order()
        self.cycle_index = [-1] * self.n
        for i, v in enumerate(self.cycle):
            self.cycle_index[v] = i

        self.root = [-1] * self.n
        self.depth = [-1] * self.n
        self.weighted_depth = [0] * self.n
        self.parent = [-1] * self.n
        self.parent_edge = [-1] * self.n
        q = deque(self.cycle)
        for v in self.cycle:
            self.root[v] = v
            self.depth[v] = 0

        while q:
            v = q.popleft()
            for u, e in graph.graph[v]:
                if self.on_cycle[u] or self.depth[u] != -1:
                    continue
                self.root[u] = self.root[v]
                self.depth[u] = self.depth[v] + 1
                self.weighted_depth[u] = self.weighted_depth[v] + int(graph.wt[e])
                self.parent[u] = v
                self.parent_edge[u] = e
                q.append(u)

        if any(d == -1 for d in self.depth):
            raise ValueError('graph must be connected')

        self.branches: list[list[int]] = [[] for _ in range(len(self.cycle))]
        for v in range(self.n):
            self.branches[self.cycle_index[self.root[v]]].append(v)
        self.cycle_prefix_weight = [0]
        for e in self.cycle_edges:
            self.cycle_prefix_weight.append(self.cycle_prefix_weight[-1] + int(graph.wt[e]))
        self._build_branch_forest()

    def _validate_connected(self) -> None:
        seen = [False] * self.n
        stack = [0]
        seen[0] = True
        count = 1
        while stack:
            v = stack.pop()
            for u, _ in self.graph.graph[v]:
                if seen[u]:
                    continue
                seen[u] = True
                count += 1
                stack.append(u)
        if count != self.n:
            raise ValueError('Namori requires a connected graph')

    def _build_cycle_order(self) -> tuple[list[int], list[int]]:
        start = next(v for v in range(self.n) if self.on_cycle[v])
        cycle: list[int] = []
        cycle_edges: list[int] = []
        visited = [False] * self.n
        v = start
        prev_edge = -1
        while True:
            if visited[v]:
                if v != start:
                    raise ValueError('cycle extraction failed')
                break
            visited[v] = True
            cycle.append(v)
            nxt = None
            for u, e in self.graph.graph[v]:
                if not self.on_cycle[u] or e == prev_edge:
                    continue
                if not visited[u] or u == start:
                    nxt = (u, e)
                    break
            if nxt is None:
                raise ValueError('cycle extraction failed')
            cycle_edges.append(nxt[1])
            v, prev_edge = nxt
        if sum(self.on_cycle) != len(cycle):
            raise ValueError('graph is not a single simple cycle with trees attached')
        if len(cycle_edges) != len(cycle):
            raise ValueError('cycle extraction failed')
        return cycle, cycle_edges

    def _validate_vertex(self, v: int) -> None:
        if not 0 <= v < self.n:
            raise IndexError('vertex index out of range')

    def _build_branch_forest(self) -> None:
        self._forest = _RootedForestData(self.n, self.parent, self.parent_edge, self.depth, self.weighted_depth, self.root)
        self.branch_children = self._forest.branch_children
        self.branch_order = self._forest.branch_order
        self.branch_tin = self._forest.branch_tin
        self.branch_tout = self._forest.branch_tout
        self.branch_size = self._forest.branch_size
        self.branch_heavy = self._forest.branch_heavy
        self.branch_hld_id = self._forest.branch_hld_id
        self.branch_hld_top = self._forest.branch_hld_top
        self.branch_hld_rev = self._forest.branch_hld_rev

    def is_on_cycle(self, v: int) -> bool:
        """
        Return whether ``v`` belongs to the unique cycle.

        Args:
            v: Query vertex.

        Returns:
            bool: Whether ``v`` is on the cycle.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> Namori(g).is_on_cycle(3)
            False
        """
        self._validate_vertex(v)
        return self.on_cycle[v]

    def cycle_hops(self, u: int, v: int) -> int:
        """
        Return the shorter distance along the cycle between two cycle vertices.

        Args:
            u: First cycle vertex.
            v: Second cycle vertex.

        Returns:
            int: Minimum number of cycle edges between ``u`` and ``v``.

        Raises:
            IndexError: If either vertex is out of range.
            ValueError: If either vertex is not on the cycle.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 3)
            >>> g.add_edge(3, 0)
            >>> g.add_edge(1, 4)
            >>> Namori(g).cycle_hops(0, 2)
            2
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if not self.on_cycle[u] or not self.on_cycle[v]:
            raise ValueError('cycle_hops() requires cycle vertices')
        diff = abs(self.cycle_index[u] - self.cycle_index[v])
        return min(diff, len(self.cycle) - diff)

    def cycle_dist(self, u: int, v: int) -> int:
        """
        Return the shorter weighted distance along the cycle between two cycle vertices.

        Args:
            u: First cycle vertex.
            v: Second cycle vertex.

        Returns:
            int: Minimum total edge weight on the cycle between ``u`` and ``v``.

        Raises:
            IndexError: If either vertex is out of range.
            ValueError: If either vertex is not on the cycle.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1, 2)
            >>> g.add_edge(1, 2, 3)
            >>> g.add_edge(2, 3, 5)
            >>> g.add_edge(3, 0, 7)
            >>> Namori(g).cycle_dist(0, 2)
            5
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if not self.on_cycle[u] or not self.on_cycle[v]:
            raise ValueError('cycle_dist() requires cycle vertices')
        iu = self.cycle_index[u]
        iv = self.cycle_index[v]
        if iu > iv:
            iu, iv = iv, iu
        forward = self.cycle_prefix_weight[iv] - self.cycle_prefix_weight[iu]
        total = self.cycle_prefix_weight[-1]
        return min(forward, total - forward)

    def cycle_root(self, v: int) -> int:
        """
        Return the cycle vertex to which ``v`` is attached.

        Args:
            v: Query vertex.

        Returns:
            int: Cycle vertex reached by repeatedly moving toward the cycle.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> Namori(g).cycle_root(3)
            1
        """
        self._validate_vertex(v)
        return self.root[v]

    def hops_to_cycle(self, v: int) -> int:
        """
        Return the distance from ``v`` to the cycle.

        Args:
            v: Query vertex.

        Returns:
            int: Number of edges from ``v`` to the cycle.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> Namori(g).hops_to_cycle(3)
            1
        """
        self._validate_vertex(v)
        return self.depth[v]

    def same_branch(self, u: int, v: int) -> bool:
        """
        Return whether ``u`` and ``v`` belong to the same attached tree.

        Cycle vertices are treated as roots of distinct branches.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            bool: Whether both vertices share the same cycle root.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> g.add_edge(3, 4)
            >>> Namori(g).same_branch(3, 4)
            True
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        return self.root[u] == self.root[v]

    def is_ancestor_in_branch(self, ancestor: int, v: int) -> bool:
        """
        Return whether ``ancestor`` is an ancestor of ``v`` in the branch forest.

        Args:
            ancestor: Candidate ancestor in the forest obtained by removing cycle edges.
            v: Query vertex.

        Returns:
            bool: Whether ``ancestor`` is on the unique branch path from the cycle root to ``v``.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> g.add_edge(3, 4)
            >>> namori = Namori(g)
            >>> namori.is_ancestor_in_branch(1, 4)
            True
        """
        self._validate_vertex(ancestor)
        self._validate_vertex(v)
        return self._forest.is_ancestor(ancestor, v)

    def subtree_range(self, v: int) -> tuple[int, int]:
        """
        Return the Euler-tour interval of ``v`` in the branch forest.

        Args:
            v: Root of the queried subtree.

        Returns:
            tuple[int, int]: Half-open interval ``[l, r)`` in ``branch_order``.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> g.add_edge(3, 4)
            >>> namori = Namori(g)
            >>> l, r = namori.subtree_range(3)
            >>> sorted(namori.branch_order[l:r])
            [3, 4]
        """
        self._validate_vertex(v)
        return self._forest.subtree_range(v)

    def branch_path_ranges(self, u: int, v: int, edge_query: bool = False) -> list[tuple[int, int]] | None:
        """
        Return HLD segments covering the branch path between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.
            edge_query: Whether to shift the left end on the final segment for edge queries.

        Returns:
            list[tuple[int, int]] | None: Half-open intervals in ``branch_hld_id`` order,
            or ``None`` if the vertices belong to different branches.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> g.add_edge(3, 4)
            >>> Namori(g).branch_path_ranges(1, 4)
            [(1, 4)]
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        return self._forest.path_ranges(u, v, edge_query)

    def branch_lca(self, u: int, v: int) -> int | None:
        """
        Return the lowest common ancestor of two vertices inside one branch tree.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            int | None: Lowest common ancestor in the branch forest, or ``None`` if the
            vertices belong to different branches.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> g.add_edge(3, 4)
            >>> Namori(g).branch_lca(3, 4)
            3
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        return self._forest.lca(u, v)

    def hops(self, u: int, v: int) -> int:
        """
        Return the shortest-path distance between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            int: Minimum number of edges on a path from ``u`` to ``v``.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> g.add_edge(3, 4)
            >>> Namori(g).hops(4, 2)
            3
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.root[u] == self.root[v]:
            lca = self.branch_lca(u, v)
            assert lca is not None
            return self.depth[u] + self.depth[v] - 2 * self.depth[lca]
        return self.depth[u] + self.depth[v] + self.cycle_hops(self.root[u], self.root[v])

    def dist(self, u: int, v: int) -> int:
        """
        Return the minimum weighted distance between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            int: Minimum total edge weight on a path from ``u`` to ``v``.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1, 2)
            >>> g.add_edge(1, 2, 3)
            >>> g.add_edge(2, 0, 10)
            >>> g.add_edge(1, 3, 4)
            >>> g.add_edge(3, 4, 5)
            >>> Namori(g).dist(4, 2)
            12
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.root[u] == self.root[v]:
            lca = self.branch_lca(u, v)
            assert lca is not None
            return self.weighted_depth[u] + self.weighted_depth[v] - 2 * self.weighted_depth[lca]
        return self.weighted_depth[u] + self.weighted_depth[v] + self.cycle_dist(self.root[u], self.root[v])

    def path_length(self, u: int, v: int) -> tuple[int, int]:
        """
        Return the lengths of the simple paths between two vertices.

        If the vertices lie in the same branch, the graph has a unique simple
        path between them and both returned values are equal. Otherwise the two
        returned values correspond to the shorter and longer choices of cycle arc.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            tuple[int, int]: Pair ``(shorter, longer)`` of simple-path lengths.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 3)
            >>> g.add_edge(3, 0)
            >>> g.add_edge(1, 4)
            >>> Namori(g).path_length(4, 3)
            (3, 3)
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.root[u] == self.root[v]:
            d = self.hops(u, v)
            return d, d
        diff = abs(self.cycle_index[self.root[u]] - self.cycle_index[self.root[v]])
        cycle_short = min(diff, len(self.cycle) - diff)
        cycle_long = max(diff, len(self.cycle) - diff)
        base = self.depth[u] + self.depth[v]
        return base + cycle_short, base + cycle_long

    def weighted_path_length(self, u: int, v: int) -> tuple[int, int]:
        """
        Return the weighted lengths of the simple paths between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            tuple[int, int]: Pair ``(shorter, longer)`` of weighted simple-path lengths.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1, 2)
            >>> g.add_edge(1, 2, 3)
            >>> g.add_edge(2, 0, 10)
            >>> g.add_edge(1, 3, 4)
            >>> g.add_edge(3, 4, 5)
            >>> Namori(g).weighted_path_length(4, 2)
            (12, 21)
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.root[u] == self.root[v]:
            d = self.dist(u, v)
            return d, d
        iu = self.cycle_index[self.root[u]]
        iv = self.cycle_index[self.root[v]]
        if iu > iv:
            iu, iv = iv, iu
        cycle_forward = self.cycle_prefix_weight[iv] - self.cycle_prefix_weight[iu]
        cycle_total = self.cycle_prefix_weight[-1]
        cycle_backward = cycle_total - cycle_forward
        base = self.weighted_depth[u] + self.weighted_depth[v]
        return base + min(cycle_forward, cycle_backward), base + max(cycle_forward, cycle_backward)


class Pseudotree:
    """
    Undirected graph whose every connected component has at most one cycle.

    Cycle components are decomposed like ``Namori``. Tree components are rooted
    at an arbitrary representative vertex and share the same branch-forest API.

    Attributes:
        graph: Original undirected graph.
        n: Number of vertices.
        component_id: Connected-component id of each vertex.
        components: Vertices of each connected component.
        component_has_cycle: Whether each component contains a cycle.
        on_cycle: Whether each vertex belongs to a cycle of its component.
        cycle_index: Position on the component cycle for cycle vertices, otherwise ``-1``.
        root: Cycle root of each vertex, or the chosen component root for tree components.
        depth: Distance from ``root`` in edges.
        weighted_depth: Weighted distance from ``root``.
        parent: Parent toward ``root``, or ``-1`` at roots.
        parent_edge: Edge to the parent, or ``-1`` at roots.
        branch_children: Children in the rooted forest.
        branch_order: Euler-tour preorder of the rooted forest.
        branch_tin: Entry time of each vertex in ``branch_order``.
        branch_tout: Exit time of each vertex as a half-open interval end.
        branch_size: Size of each subtree in the rooted forest.
        branch_hld_id: Position of each vertex in branch HLD order.
        branch_hld_rev: Inverse map of ``branch_hld_id``.
        branch_hld_top: Head vertex of the heavy path containing each vertex.
        branch_heavy: Heavy child of each vertex, or ``-1``.

    Space Complexity:
        O(n)

    Examples:
        >>> g = Graph(7)
        >>> g.add_edge(0, 1)
        >>> g.add_edge(1, 2)
        >>> g.add_edge(2, 0)
        >>> g.add_edge(1, 3)
        >>> g.add_edge(4, 5)
        >>> g.add_edge(5, 6)
        >>> pt = Pseudotree(g)
        >>> pt.has_cycle(0)
        True
        >>> pt.has_cycle(4)
        False
    """

    def __init__(self, graph: Graph) -> None:
        """
        Build a pseudotree decomposition from an undirected graph.

        Args:
            graph: Undirected graph whose every connected component has at most one cycle.

        Returns:
            None: This constructor initializes the decomposition in place.

        Raises:
            ValueError: If the graph is directed or some connected component contains two or more cycles.

        Time Complexity:
            O(n + m)

        Examples:
            >>> g = Graph(6)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(3, 4)
            >>> g.add_edge(4, 5)
            >>> pt = Pseudotree(g)
            >>> pt.same_component(3, 5)
            True
        """
        if graph.is_directed:
            raise ValueError('Pseudotree requires an undirected graph')
        self.graph = graph
        self.n = graph.n

        self.component_id = [-1] * self.n
        self.components: list[list[int]] = []
        self.component_edge_count: list[int] = []
        self.component_has_cycle: list[bool] = []
        self.component_cycle_vertices: list[list[int]] = []
        self.component_cycle_edges: list[list[int]] = []
        self._component_cycle_prefix_weight: list[list[int]] = []
        self._component_namori: list[_ComponentNamoriAdapter | None] = []
        self._build_components()

        deg = [len(adj) for adj in graph.graph]
        removed = [False] * self.n
        q = deque(v for v in range(self.n) if deg[v] <= 1)
        while q:
            v = q.popleft()
            if removed[v]:
                continue
            removed[v] = True
            for u, _ in graph.graph[v]:
                if removed[u]:
                    continue
                deg[u] -= 1
                if deg[u] == 1:
                    q.append(u)

        self.on_cycle = [False] * self.n
        self.cycle_index = [-1] * self.n
        for cid, vertices in enumerate(self.components):
            cyc = [v for v in vertices if not removed[v]]
            has_cycle = len(cyc) > 0
            self.component_has_cycle.append(has_cycle)
            if has_cycle:
                adapter = _ComponentNamoriAdapter(graph, vertices)
                self._component_namori.append(adapter)
                self.component_cycle_vertices.append(adapter.cycle)
                self.component_cycle_edges.append(adapter.cycle_edges)
                self._component_cycle_prefix_weight.append(adapter.cycle_prefix_weight)
                for i, v in enumerate(adapter.cycle):
                    self.on_cycle[v] = True
                    self.cycle_index[v] = i
            else:
                self._component_namori.append(None)
                self.component_cycle_vertices.append([])
                self.component_cycle_edges.append([])
                self._component_cycle_prefix_weight.append([0])

        self.root = [-1] * self.n
        self.depth = [-1] * self.n
        self.weighted_depth = [0] * self.n
        self.parent = [-1] * self.n
        self.parent_edge = [-1] * self.n
        seeds: list[int] = []
        for cid, vertices in enumerate(self.components):
            if self.component_has_cycle[cid]:
                for v in self.component_cycle_vertices[cid]:
                    self.root[v] = v
                    self.depth[v] = 0
                    seeds.append(v)
            elif vertices:
                root = vertices[0]
                self.root[root] = root
                self.depth[root] = 0
                seeds.append(root)

        q = deque(seeds)
        while q:
            v = q.popleft()
            for u, e in graph.graph[v]:
                if self.depth[u] != -1:
                    continue
                self.root[u] = self.root[v]
                self.depth[u] = self.depth[v] + 1
                self.weighted_depth[u] = self.weighted_depth[v] + int(graph.wt[e])
                self.parent[u] = v
                self.parent_edge[u] = e
                q.append(u)

        self._build_branch_forest()

    def _build_components(self) -> None:
        seen = [False] * self.n
        for start in range(self.n):
            if seen[start]:
                continue
            stack = [start]
            seen[start] = True
            vertices: list[int] = []
            edge_count = 0
            while stack:
                v = stack.pop()
                self.component_id[v] = len(self.components)
                vertices.append(v)
                edge_count += len(self.graph.graph[v])
                for u, _ in self.graph.graph[v]:
                    if seen[u]:
                        continue
                    seen[u] = True
                    stack.append(u)
            edge_count //= 2
            if edge_count > len(vertices):
                raise ValueError('each connected component must contain at most one cycle')
            self.components.append(vertices)
            self.component_edge_count.append(edge_count)

    def _build_branch_forest(self) -> None:
        self._forest = _RootedForestData(self.n, self.parent, self.parent_edge, self.depth, self.weighted_depth, self.root)
        self.branch_children = self._forest.branch_children
        self.branch_order = self._forest.branch_order
        self.branch_tin = self._forest.branch_tin
        self.branch_tout = self._forest.branch_tout
        self.branch_size = self._forest.branch_size
        self.branch_heavy = self._forest.branch_heavy
        self.branch_hld_id = self._forest.branch_hld_id
        self.branch_hld_top = self._forest.branch_hld_top
        self.branch_hld_rev = self._forest.branch_hld_rev

    def _validate_vertex(self, v: int) -> None:
        if not 0 <= v < self.n:
            raise IndexError('vertex index out of range')

    def component_of(self, v: int) -> int:
        """
        Return the connected-component id of ``v``.

        Args:
            v: Query vertex.

        Returns:
            int: Zero-based connected-component id.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(2)
            >>> pt = Pseudotree(g)
            >>> pt.component_of(1)
            1
        """
        self._validate_vertex(v)
        return self.component_id[v]

    def same_component(self, u: int, v: int) -> bool:
        """
        Return whether two vertices belong to the same connected component.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            bool: Whether ``u`` and ``v`` are connected.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> pt = Pseudotree(g)
            >>> pt.same_component(0, 2)
            False
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        return self.component_id[u] == self.component_id[v]

    def has_cycle(self, v: int) -> bool:
        """
        Return whether the component containing ``v`` has a cycle.

        Args:
            v: Query vertex.

        Returns:
            bool: Whether the connected component of ``v`` is unicyclic.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> pt = Pseudotree(g)
            >>> pt.has_cycle(1)
            True
        """
        self._validate_vertex(v)
        return self.component_has_cycle[self.component_id[v]]

    def component_cycle(self, v: int) -> list[int]:
        """
        Return the cycle of the component containing ``v``.

        Args:
            v: Query vertex.

        Returns:
            list[int]: Cycle vertices in cyclic order, or an empty list for a tree component.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> Pseudotree(g).component_cycle(0)
            [0, 1, 2]
        """
        self._validate_vertex(v)
        return self.component_cycle_vertices[self.component_id[v]]

    def is_on_cycle(self, v: int) -> bool:
        """
        Return whether ``v`` belongs to a cycle of its component.

        Args:
            v: Query vertex.

        Returns:
            bool: Whether ``v`` is on the component cycle.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> Pseudotree(g).is_on_cycle(3)
            False
        """
        self._validate_vertex(v)
        return self.on_cycle[v]

    def cycle_root(self, v: int) -> int:
        """
        Return the cycle vertex to which ``v`` is attached.

        Args:
            v: Query vertex.

        Returns:
            int: Cycle vertex reached by moving toward the cycle.

        Raises:
            IndexError: If ``v`` is out of range.
            ValueError: If the component containing ``v`` is a tree.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> Pseudotree(g).cycle_root(3)
            1
        """
        self._validate_vertex(v)
        if not self.has_cycle(v):
            raise ValueError('cycle_root() requires a unicyclic component')
        adapter = self._component_namori[self.component_id[v]]
        assert adapter is not None
        return adapter.cycle_root(v)

    def hops_to_cycle(self, v: int) -> int:
        """
        Return the distance from ``v`` to the cycle of its component.

        Args:
            v: Query vertex.

        Returns:
            int: Number of edges from ``v`` to the cycle.

        Raises:
            IndexError: If ``v`` is out of range.
            ValueError: If the component containing ``v`` is a tree.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> Pseudotree(g).hops_to_cycle(3)
            1
        """
        self._validate_vertex(v)
        if not self.has_cycle(v):
            raise ValueError('hops_to_cycle() requires a unicyclic component')
        adapter = self._component_namori[self.component_id[v]]
        assert adapter is not None
        return adapter.hops_to_cycle(v)

    def same_branch(self, u: int, v: int) -> bool:
        """
        Return whether ``u`` and ``v`` belong to the same rooted branch.

        In a tree component, the entire component is treated as one branch.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            bool: Whether both vertices share the same branch root.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> g.add_edge(3, 4)
            >>> Pseudotree(g).same_branch(3, 4)
            True
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        return self.component_id[u] == self.component_id[v] and self.root[u] == self.root[v]

    def is_ancestor_in_branch(self, ancestor: int, v: int) -> bool:
        """
        Return whether ``ancestor`` is an ancestor of ``v`` in the rooted forest.

        Args:
            ancestor: Candidate ancestor.
            v: Query vertex.

        Returns:
            bool: Whether ``ancestor`` lies on the rooted path to ``v``.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> pt = Pseudotree(g)
            >>> pt.is_ancestor_in_branch(0, 2)
            True
        """
        self._validate_vertex(ancestor)
        self._validate_vertex(v)
        return self._forest.is_ancestor(ancestor, v)

    def subtree_range(self, v: int) -> tuple[int, int]:
        """
        Return the Euler-tour interval of ``v`` in the rooted forest.

        Args:
            v: Root of the queried subtree.

        Returns:
            tuple[int, int]: Half-open interval ``[l, r)`` in ``branch_order``.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> pt = Pseudotree(g)
            >>> pt.subtree_range(1)
            (1, 3)
        """
        self._validate_vertex(v)
        return self._forest.subtree_range(v)

    def branch_path_ranges(self, u: int, v: int, edge_query: bool = False) -> list[tuple[int, int]] | None:
        """
        Return HLD segments covering the rooted-forest path between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.
            edge_query: Whether to shift the left end on the final segment for edge queries.

        Returns:
            list[tuple[int, int]] | None: Half-open intervals in ``branch_hld_id`` order,
            or ``None`` if the vertices do not share a branch root.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> pt = Pseudotree(g)
            >>> pt.branch_path_ranges(0, 2)
            [(0, 3)]
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        return self._forest.path_ranges(u, v, edge_query)

    def branch_lca(self, u: int, v: int) -> int | None:
        """
        Return the lowest common ancestor inside one rooted branch.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            int | None: Lowest common ancestor, or ``None`` if the vertices do not share a branch root.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> Pseudotree(g).branch_lca(1, 2)
            1
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        return self._forest.lca(u, v)

    def cycle_hops(self, u: int, v: int) -> int:
        """
        Return the shorter distance along the component cycle between two cycle vertices.

        Args:
            u: First cycle vertex.
            v: Second cycle vertex.

        Returns:
            int: Minimum number of cycle edges between ``u`` and ``v``.

        Raises:
            IndexError: If either vertex is out of range.
            ValueError: If the vertices are not on the same component cycle.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 3)
            >>> g.add_edge(3, 0)
            >>> Pseudotree(g).cycle_hops(0, 2)
            2
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.component_id[u] != self.component_id[v] or not self.on_cycle[u] or not self.on_cycle[v]:
            raise ValueError('cycle_hops() requires two cycle vertices in the same component')
        adapter = self._component_namori[self.component_id[u]]
        assert adapter is not None
        return adapter.cycle_hops(u, v)

    def cycle_dist(self, u: int, v: int) -> int:
        """
        Return the shorter weighted distance along the component cycle between two cycle vertices.

        Args:
            u: First cycle vertex.
            v: Second cycle vertex.

        Returns:
            int: Minimum total edge weight on the cycle between ``u`` and ``v``.

        Raises:
            IndexError: If either vertex is out of range.
            ValueError: If the vertices are not on the same component cycle.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1, 2)
            >>> g.add_edge(1, 2, 3)
            >>> g.add_edge(2, 3, 5)
            >>> g.add_edge(3, 0, 7)
            >>> Pseudotree(g).cycle_dist(0, 2)
            5
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.component_id[u] != self.component_id[v] or not self.on_cycle[u] or not self.on_cycle[v]:
            raise ValueError('cycle_dist() requires two cycle vertices in the same component')
        adapter = self._component_namori[self.component_id[u]]
        assert adapter is not None
        return adapter.cycle_dist(u, v)

    def hops(self, u: int, v: int) -> int:
        """
        Return the shortest-path distance between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            int: Minimum number of edges on a path from ``u`` to ``v``.

        Raises:
            IndexError: If either vertex is out of range.
            ValueError: If the vertices belong to different connected components.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> Pseudotree(g).hops(0, 2)
            2
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.component_id[u] != self.component_id[v]:
            raise ValueError('hops() requires vertices in the same component')
        adapter = self._component_namori[self.component_id[u]]
        if adapter is not None:
            return adapter.hops(u, v)
        if self.root[u] == self.root[v]:
            lca = self.branch_lca(u, v)
            assert lca is not None
            return self.depth[u] + self.depth[v] - 2 * self.depth[lca]
        raise AssertionError('unreachable')

    def dist(self, u: int, v: int) -> int:
        """
        Return the minimum weighted distance between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            int: Minimum total edge weight on a path from ``u`` to ``v``.

        Raises:
            IndexError: If either vertex is out of range.
            ValueError: If the vertices belong to different connected components.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1, 2)
            >>> g.add_edge(1, 2, 5)
            >>> Pseudotree(g).dist(0, 2)
            7
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.component_id[u] != self.component_id[v]:
            raise ValueError('dist() requires vertices in the same component')
        adapter = self._component_namori[self.component_id[u]]
        if adapter is not None:
            return adapter.dist(u, v)
        if self.root[u] == self.root[v]:
            lca = self.branch_lca(u, v)
            assert lca is not None
            return self.weighted_depth[u] + self.weighted_depth[v] - 2 * self.weighted_depth[lca]
        raise AssertionError('unreachable')

    def path_length(self, u: int, v: int) -> tuple[int, int]:
        """
        Return the lengths of the simple paths between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            tuple[int, int]: Pair ``(shorter, longer)`` of simple-path lengths.

        Raises:
            IndexError: If either vertex is out of range.
            ValueError: If the vertices belong to different connected components.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 3)
            >>> g.add_edge(3, 0)
            >>> g.add_edge(1, 4)
            >>> Pseudotree(g).path_length(4, 3)
            (3, 3)
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.component_id[u] != self.component_id[v]:
            raise ValueError('path_length() requires vertices in the same component')
        adapter = self._component_namori[self.component_id[u]]
        if adapter is not None:
            return adapter.path_length(u, v)
        if not self.component_has_cycle[self.component_id[u]] or self.root[u] == self.root[v]:
            d = self.hops(u, v)
            return d, d
        raise AssertionError('unreachable')

    def weighted_path_length(self, u: int, v: int) -> tuple[int, int]:
        """
        Return the weighted lengths of the simple paths between two vertices.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            tuple[int, int]: Pair ``(shorter, longer)`` of weighted simple-path lengths.

        Raises:
            IndexError: If either vertex is out of range.
            ValueError: If the vertices belong to different connected components.

        Time Complexity:
            O(log n)

        Examples:
            >>> g = Graph(5)
            >>> g.add_edge(0, 1, 2)
            >>> g.add_edge(1, 2, 3)
            >>> g.add_edge(2, 0, 10)
            >>> g.add_edge(1, 3, 4)
            >>> g.add_edge(3, 4, 5)
            >>> Pseudotree(g).weighted_path_length(4, 2)
            (12, 21)
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if self.component_id[u] != self.component_id[v]:
            raise ValueError('weighted_path_length() requires vertices in the same component')
        adapter = self._component_namori[self.component_id[u]]
        if adapter is not None:
            return adapter.weighted_path_length(u, v)
        if not self.component_has_cycle[self.component_id[u]] or self.root[u] == self.root[v]:
            d = self.dist(u, v)
            return d, d
        raise AssertionError('unreachable')


class CactusGraph:
    """
    Undirected cactus graph decomposition.

    Every edge belongs to at most one simple cycle. The graph may be
    disconnected. Each biconnected block is represented either as a bridge
    block or as a simple cycle block.

    Attributes:
        graph: Original undirected graph.
        n: Number of vertices.
        block_vertices: Vertices contained in each block.
        block_edges: Edge ids contained in each block.
        block_has_cycle: Whether each block is a cycle block.
        block_cycle: Cycle vertices of each cycle block in cyclic order, or an
            empty list for a bridge block.
        block_cycle_edges: Cycle edge ids aligned with ``block_cycle``.
        vertex_blocks: Incident block ids of each vertex.
        edge_block: Block id containing each edge.
        articulation: Whether each vertex is an articulation point.
        on_cycle: Whether each vertex lies on at least one cycle.
        block_cut_forest: Adjacency list of the block-cut forest.
        component_id: Connected-component id of each original vertex.
        components: Vertices of each connected component.

    Space Complexity:
        O(n + m)

    Examples:
        >>> g = Graph(5)
        >>> g.add_edge(0, 1)
        >>> g.add_edge(1, 2)
        >>> g.add_edge(2, 0)
        >>> g.add_edge(1, 3)
        >>> g.add_edge(3, 4)
        >>> cactus = CactusGraph(g)
        >>> cactus.is_on_cycle(1)
        True
        >>> sum(cactus.is_cycle_block(i) for i in range(len(cactus.block_cycle)))
        1
    """

    def __init__(self, graph: Graph) -> None:
        """
        Build a cactus decomposition from an undirected graph.

        Args:
            graph: Undirected cactus graph.

        Returns:
            None: This constructor initializes the decomposition in place.

        Raises:
            ValueError: If the graph is directed or is not a cactus graph.

        Time Complexity:
            O(n + m)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> cactus = CactusGraph(g)
            >>> cactus.blocks_of(1)
            [0, 1]
        """
        if graph.is_directed:
            raise ValueError('CactusGraph requires an undirected graph')
        self.graph = graph
        self.n = graph.n

        analysis = analyze_lowlink(graph)
        self.articulation = analysis.articulation
        self.block_vertices = [list(map(int, comp)) for comp in analysis.biconnected_components]
        self.vertex_blocks: list[list[int]] = [[] for _ in range(self.n)]
        for bid, vertices in enumerate(self.block_vertices):
            for v in vertices:
                self.vertex_blocks[v].append(bid)

        self.edge_block = [-1] * graph.m
        common_count: dict[tuple[int, int], int] = {}
        for v in range(self.n):
            for bid in self.vertex_blocks[v]:
                common_count[(v, bid)] = 1
        self.block_edges: list[list[int]] = [[] for _ in range(len(self.block_vertices))]
        for e, (u, v) in enumerate(graph.edges):
            assigned = -1
            if len(self.vertex_blocks[u]) < len(self.vertex_blocks[v]):
                candidates = self.vertex_blocks[u]
                other = set(self.vertex_blocks[v])
            else:
                candidates = self.vertex_blocks[v]
                other = set(self.vertex_blocks[u])
            for bid in candidates:
                if bid in other:
                    assigned = bid
                    break
            if assigned == -1:
                raise ValueError('failed to assign an edge to a biconnected block')
            self.edge_block[e] = assigned
            self.block_edges[assigned].append(e)

        self.block_has_cycle: list[bool] = [False] * len(self.block_vertices)
        self.block_cycle: list[list[int]] = [[] for _ in range(len(self.block_vertices))]
        self.block_cycle_edges: list[list[int]] = [[] for _ in range(len(self.block_vertices))]
        self._block_cycle_prefix_weight: list[list[int]] = [[0] for _ in range(len(self.block_vertices))]
        self.on_cycle = [False] * self.n

        for bid, vertices in enumerate(self.block_vertices):
            edges = self.block_edges[bid]
            if len(vertices) == 1 and len(edges) == 0:
                continue
            if len(edges) == 1 and len(vertices) == 2:
                continue
            local_deg = {v: 0 for v in vertices}
            for e in edges:
                u, v = graph.edges[e]
                if int(u) not in local_deg or int(v) not in local_deg:
                    raise ValueError('block-edge assignment is inconsistent')
                local_deg[int(u)] += 1
                local_deg[int(v)] += 1
            if len(edges) != len(vertices) or any(d != 2 for d in local_deg.values()):
                raise ValueError('graph is not a cactus graph')
            self.block_has_cycle[bid] = True
            cycle, cycle_edges = self._build_cycle_for_block(bid)
            self.block_cycle[bid] = cycle
            self.block_cycle_edges[bid] = cycle_edges
            prefix = [0]
            for e in cycle_edges:
                prefix.append(prefix[-1] + int(graph.wt[e]))
            self._block_cycle_prefix_weight[bid] = prefix
            for v in cycle:
                self.on_cycle[v] = True

        bc = block_cut_tree(graph)
        self.block_cut_forest = bc.graph

        self.component_id = [-1] * self.n
        self.components: list[list[int]] = []
        for start in range(self.n):
            if self.component_id[start] != -1:
                continue
            cid = len(self.components)
            stack = [start]
            self.component_id[start] = cid
            comp: list[int] = []
            while stack:
                v = stack.pop()
                comp.append(v)
                for u, _ in graph.graph[v]:
                    if self.component_id[u] != -1:
                        continue
                    self.component_id[u] = cid
                    stack.append(u)
            self.components.append(comp)

    def _build_cycle_for_block(self, bid: int) -> tuple[list[int], list[int]]:
        block_vertices = set(self.block_vertices[bid])
        start = self.block_vertices[bid][0]
        cycle: list[int] = []
        cycle_edges: list[int] = []
        visited = {v: False for v in block_vertices}
        v = start
        prev_edge = -1
        while True:
            if visited[v]:
                if v != start:
                    raise ValueError('failed to reconstruct a cycle block')
                break
            visited[v] = True
            cycle.append(v)
            nxt = None
            for u, e in self.graph.graph[v]:
                if int(u) not in block_vertices or int(e) == prev_edge:
                    continue
                if not visited[int(u)] or int(u) == start:
                    nxt = (int(u), int(e))
                    break
            if nxt is None:
                raise ValueError('failed to reconstruct a cycle block')
            cycle_edges.append(nxt[1])
            v, prev_edge = nxt
        if len(cycle) != len(block_vertices) or len(cycle_edges) != len(cycle):
            raise ValueError('failed to reconstruct a cycle block')
        return cycle, cycle_edges

    def _validate_vertex(self, v: int) -> None:
        if not 0 <= v < self.n:
            raise IndexError('vertex index out of range')

    def _validate_block(self, block: int) -> None:
        if not 0 <= block < len(self.block_vertices):
            raise IndexError('block index out of range')

    def _validate_edge(self, edge: int) -> None:
        if not 0 <= edge < self.graph.m:
            raise IndexError('edge index out of range')

    def blocks_of(self, v: int) -> list[int]:
        """
        Return the block ids incident to ``v``.

        Args:
            v: Query vertex.

        Returns:
            list[int]: Incident block ids.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(deg(v))

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> CactusGraph(g).blocks_of(1)
            [0, 1]
        """
        self._validate_vertex(v)
        return self.vertex_blocks[v][:]

    def block_of_edge(self, edge: int) -> int:
        """
        Return the block id containing one edge.

        Args:
            edge: Original edge id.

        Returns:
            int: Block id containing ``edge``.

        Raises:
            IndexError: If ``edge`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> CactusGraph(g).block_of_edge(0)
            0
        """
        self._validate_edge(edge)
        return self.edge_block[edge]

    def is_articulation(self, v: int) -> bool:
        """
        Return whether ``v`` is an articulation point.

        Args:
            v: Query vertex.

        Returns:
            bool: Whether removing ``v`` increases the number of connected components.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> CactusGraph(g).is_articulation(1)
            True
        """
        self._validate_vertex(v)
        return self.articulation[v]

    def is_on_cycle(self, v: int) -> bool:
        """
        Return whether ``v`` lies on at least one cactus cycle.

        Args:
            v: Query vertex.

        Returns:
            bool: Whether ``v`` belongs to some cycle block.

        Raises:
            IndexError: If ``v`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> CactusGraph(g).is_on_cycle(3)
            False
        """
        self._validate_vertex(v)
        return self.on_cycle[v]

    def is_cycle_block(self, block: int) -> bool:
        """
        Return whether one block is a simple cycle block.

        Args:
            block: Block id.

        Returns:
            bool: Whether ``block`` is a cycle block.

        Raises:
            IndexError: If ``block`` is out of range.

        Time Complexity:
            O(1)

        Examples:
            >>> g = Graph(2)
            >>> g.add_edge(0, 1)
            >>> CactusGraph(g).is_cycle_block(0)
            False
        """
        self._validate_block(block)
        return self.block_has_cycle[block]

    def cycle_of_block(self, block: int) -> list[int]:
        """
        Return the vertex order of a cycle block.

        Args:
            block: Block id.

        Returns:
            list[int]: Cycle vertices in cyclic order, or an empty list for a bridge block.

        Raises:
            IndexError: If ``block`` is out of range.

        Time Complexity:
            O(k)

        Space Complexity:
            O(k)

        Examples:
            >>> g = Graph(3)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> sorted(CactusGraph(g).cycle_of_block(0))
            [0, 1, 2]
        """
        self._validate_block(block)
        return self.block_cycle[block][:]

    def same_block(self, u: int, v: int) -> bool:
        """
        Return whether two vertices belong to a common block.

        Args:
            u: First query vertex.
            v: Second query vertex.

        Returns:
            bool: Whether ``u`` and ``v`` lie in the same block.

        Raises:
            IndexError: If either vertex is out of range.

        Time Complexity:
            O(min(b(u), b(v)))

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 0)
            >>> g.add_edge(1, 3)
            >>> CactusGraph(g).same_block(0, 2)
            True
        """
        self._validate_vertex(u)
        self._validate_vertex(v)
        if len(self.vertex_blocks[u]) < len(self.vertex_blocks[v]):
            other = set(self.vertex_blocks[v])
            return any(b in other for b in self.vertex_blocks[u])
        other = set(self.vertex_blocks[u])
        return any(b in other for b in self.vertex_blocks[v])

    def cycle_hops(self, block: int, u: int, v: int) -> int:
        """
        Return the shorter distance along one cycle block between two vertices.

        Args:
            block: Cycle block id.
            u: First vertex on the cycle block.
            v: Second vertex on the cycle block.

        Returns:
            int: Minimum number of cycle edges between ``u`` and ``v`` inside ``block``.

        Raises:
            IndexError: If an index is out of range.
            ValueError: If ``block`` is not a cycle block or if a vertex is not on that cycle.

        Time Complexity:
            O(k)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(2, 3)
            >>> g.add_edge(3, 0)
            >>> CactusGraph(g).cycle_hops(0, 0, 2)
            2
        """
        self._validate_block(block)
        self._validate_vertex(u)
        self._validate_vertex(v)
        if not self.block_has_cycle[block]:
            raise ValueError('cycle_hops() requires a cycle block')
        cycle = self.block_cycle[block]
        try:
            iu = cycle.index(u)
            iv = cycle.index(v)
        except ValueError as exc:
            raise ValueError('vertices must belong to the specified cycle block') from exc
        diff = abs(iu - iv)
        return min(diff, len(cycle) - diff)

    def cycle_dist(self, block: int, u: int, v: int) -> int:
        """
        Return the shorter weighted distance along one cycle block.

        Args:
            block: Cycle block id.
            u: First vertex on the cycle block.
            v: Second vertex on the cycle block.

        Returns:
            int: Minimum total edge weight between ``u`` and ``v`` inside ``block``.

        Raises:
            IndexError: If an index is out of range.
            ValueError: If ``block`` is not a cycle block or if a vertex is not on that cycle.

        Time Complexity:
            O(k)

        Examples:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1, 2)
            >>> g.add_edge(1, 2, 3)
            >>> g.add_edge(2, 3, 5)
            >>> g.add_edge(3, 0, 7)
            >>> CactusGraph(g).cycle_dist(0, 0, 2)
            5
        """
        self._validate_block(block)
        self._validate_vertex(u)
        self._validate_vertex(v)
        if not self.block_has_cycle[block]:
            raise ValueError('cycle_dist() requires a cycle block')
        cycle = self.block_cycle[block]
        try:
            iu = cycle.index(u)
            iv = cycle.index(v)
        except ValueError as exc:
            raise ValueError('vertices must belong to the specified cycle block') from exc
        if iu > iv:
            iu, iv = iv, iu
        prefix = self._block_cycle_prefix_weight[block]
        forward = prefix[iv] - prefix[iu]
        total = prefix[-1]
        return min(forward, total - forward)
