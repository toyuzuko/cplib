#!/usr/bin/env python3

from __future__ import annotations  # for library checker

from cplib.graph.base import Node, EdgeNum, Capacity, Cost
from cplib.graph.matching import MatchingSuccess

from collections import deque
from typing import NamedTuple


class MaximumFlowEdge(NamedTuple):
    """
    Edge information in maximum flow result.

    Attributes:
        source: Source vertex of the edge.
        target: Target vertex of the edge.
        capacity: Capacity of the original directed edge.
        flow: Flow currently sent through that edge.

    This record corresponds to one original edge added to the network.
    Reverse residual edges are not exposed here.
    It is intended for reporting, not for mutation.

    Space Complexity:
        O(1)
    """
    source: Node
    target: Node
    capacity: Capacity
    flow: Capacity


class MaximumFlowResult(NamedTuple):
    """
    Result of maximum flow computation.

    Attributes:
        flow: Additional flow sent by this call to ``solve``.
        edges: All original edges together with their cumulative flow values.

    The ``edges`` list preserves the edge insertion order.
    It can be used to reconstruct the final flow assignment.
    Repeated calls retain the previous flow; ``flow`` counts only the increase.

    Space Complexity:
        O(m), where m is the number of reported edges
    """
    flow: Capacity
    edges: list[MaximumFlowEdge]


class MinimumCostBFlowEdge(NamedTuple):
    """
    Edge information in minimum cost b-flow result.

    Attributes:
        source: Source vertex of the edge.
        target: Target vertex of the edge.
        lower: Lower flow bound.
        upper: Upper flow bound.
        cost: Cost per unit flow.
        flow: Flow currently assigned to the edge.

    This record corresponds to one original edge added to the network.

    Space Complexity:
        O(1)
    """
    source: Node
    target: Node
    lower: Capacity
    upper: Capacity
    cost: Cost
    flow: Capacity


class MinimumCostBFlowResult(NamedTuple):
    """
    Result of minimum cost b-flow computation.

    Attributes:
        feasible: Whether a feasible flow satisfying all constraints exists.
        cost: Minimum total cost, or ``0`` if infeasible.
        edges: All original edges together with their realized flow values.

    The ``edges`` list preserves the edge insertion order.
    Edge flows are meaningful only when ``feasible`` is true.
    The reported cost is already minimized among feasible solutions.

    Space Complexity:
        O(m), where m is the number of reported edges
    """
    feasible: bool
    cost: Cost
    edges: list[MinimumCostBFlowEdge]

class MaximumFlow:
    """
    Maximum flow solver using Dinic's algorithm with current-edge optimization.

    Dinic's algorithm finds the maximum flow from a source to a target in a flow network.
    This implementation uses level graphs and blocking flows for efficiency.

    Attributes:
        flow_inf: Class variable representing infinite capacity (default: 2^60)
        n: Number of vertices in the flow network
        m: Number of edges added to the network
        edges: List of edge tuples (from, to, capacity)
        graph: Adjacency list representation with edge indices
        flow: Current flow values for each edge

    Examples:
        >>> # Simple flow network: source -> a -> b -> target
        >>> mf = MaximumFlow(4)
        >>> source, a, b, target = 0, 1, 2, 3
        >>> mf.add_edge(source, a, 10)
        >>> mf.add_edge(a, b, 5)
        >>> mf.add_edge(b, target, 7)
        >>> mf.add_edge(a, target, 3)  # Direct path
        >>> result = mf.solve(source, target)
        >>> assert result.flow == 8  # 5 through a->b->target, 3 through a->target

        >>> # Get flow on each edge
        >>> for u, v, cap, flow in result.edges:
        ...     if flow > 0:
        ...         print(f"Edge {u}->{v}: {flow}/{cap}")
        Edge 0->1: 8/10
        Edge 1->2: 5/5
        Edge 2->3: 5/7
        Edge 1->3: 3/3

    Args:
        n: Number of elements, vertices, or rows handled by the structure.

    Complexity Notation:
        n: Number of vertices.
        m: Number of directed edges added with ``add_edge``.

    Space Complexity:
        O(n + m)
    """
    flow_inf = Capacity(1 << 60)

    def __init__(self, n: int) -> None:
        """Initialize a flow network with n vertices.

        Args:
            n: Number of vertices in the flow network (0-indexed)

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
        self.edges: list[tuple[Node, Node, Capacity]] = []
        self.flow: list[Capacity] = []
        self._start: list[int] = [0] * (n + 1)
        self._to: list[Node] = []
        self._rev: list[int] = []
        self._cap: list[int] = []
        self._forward_arc: list[int] = []

    def add_edge(self, u: Node, v: Node, cap: Capacity) -> None:
        """
        Add a directed edge with given capacity to the flow network.

        Args:
            u: Source vertex of the edge (0-indexed)
            v: Target vertex of the edge (0-indexed)
            cap: Capacity of the edge (non-negative)

        Raises:
            IndexError: If an endpoint is outside ``[0, n)``.
            ValueError: If ``cap`` is negative.

        Returns:
            ``None``.

        Notes:
            - Creates residual edges automatically
            - Edges are stored with their index for efficient updates

        Time Complexity:
            O(1)
        """
        if not 0 <= u < self.n or not 0 <= v < self.n:
            raise IndexError('edge endpoint must be within [0, n)')
        if cap < 0:
            raise ValueError('capacity must be non-negative')
        self.edges.append((u, v, cap))
        self.flow.append(Capacity(0))
        self.m += 1

    def get_edge(self, e: EdgeNum) -> tuple[Node, Node, Capacity, Capacity]:
        """
        Get information about a specific edge.

        Args:
            e: Edge index (order in which edges were added)

        Returns:
            Tuple of (from_vertex, to_vertex, capacity, flow)

        Raises:
            IndexError: If ``e`` is outside ``[0, m)``.

        Time Complexity:
            O(1)
        """
        if not 0 <= e < self.m:
            raise IndexError('edge id must be within [0, m)')
        u, v, cap = self.edges[e]
        return (u, v, cap, self.flow[e])

    def get_edges(self) -> list[tuple[Node, Node, Capacity, Capacity]]:
        """
        Get information about all edges in the network.

        Returns:
            List of tuples (from_vertex, to_vertex, capacity, flow) for each edge

        Time Complexity:
            O(m)
        """
        return [self.get_edge(EdgeNum(e)) for e in range(self.m)]

    def _build_graph(self) -> None:
        degree = [0] * self.n
        for u, v, _ in self.edges:
            degree[u] += 1
            degree[v] += 1

        start = [0] * (self.n + 1)
        for i in range(self.n):
            start[i + 1] = start[i] + degree[i]

        arc_count = start[self.n]
        to = [Node(0)] * arc_count
        rev = [0] * arc_count
        cap = [0] * arc_count
        forward_arc = [0] * self.m
        cursor = start[:]

        for e, (u, v, c) in enumerate(self.edges):
            f = self.flow[e]
            p = cursor[u]
            cursor[u] += 1
            q = cursor[v]
            cursor[v] += 1

            to[p] = v
            rev[p] = q
            cap[p] = int(c - f)
            forward_arc[e] = p

            to[q] = u
            rev[q] = p
            cap[q] = int(f)

        self._start = start
        self._to = to
        self._rev = rev
        self._cap = cap
        self._forward_arc = forward_arc

    def _sync_flow(self) -> None:
        cap = self._cap
        forward_arc = self._forward_arc
        for e, (_, _, c) in enumerate(self.edges):
            self.flow[e] = Capacity(c - cap[forward_arc[e]])

    def _bfs(self, source: Node, target: Node) -> list[int]:
        start = self._start
        to = self._to
        cap = self._cap
        que = deque([source])
        level = [-1] * self.n
        level[source] = 0
        while que:
            v = que.popleft()
            for i in range(start[v], start[v + 1]):
                c = to[i]
                if cap[i] == 0 or level[c] >= 0:
                    continue
                level[c] = level[v] + 1
                if c == target:
                    return level
                que.append(c)
        return level

    def _dfs(self, source: Node, target: Node, flow_limit: Capacity, level: list[int], work: list[int]) -> Capacity:
        start = self._start
        to = self._to
        rev = self._rev
        cap = self._cap
        stack = [target]
        while stack:
            v = stack.pop()
            if v == source:
                f = int(flow_limit)
                for v in stack:
                    f = min(f, cap[rev[work[v]]])
                for v in stack:
                    e = work[v]
                    r = rev[e]
                    cap[r] -= f
                    cap[e] += f
                return Capacity(f)
            lv = level[v]
            for i in range(work[v], start[v + 1]):
                c = to[i]
                if lv > level[c] and cap[rev[i]] > 0:
                    work[v] = i
                    stack.append(v)
                    stack.append(c)
                    break
            else:
                work[v] = start[v + 1]
                level[v] = self.n
        return Capacity(0)

    def solve(self, source: Node, target: Node, flow_limit: Capacity | None = None) -> MaximumFlowResult:
        """
        Find the maximum flow from source to target using Dinic's algorithm.

        Args:
            source: Source vertex (0-indexed)
            target: Target vertex (0-indexed)
            flow_limit: Upper bound on additional flow in this call. Defaults
                to ``flow_inf`` (``2**60``).

        Returns:
            MaximumFlowResult containing:
            - flow: Additional flow sent in this call
            - edges: List of all edges with their cumulative flow values

        Raises:
            IndexError: If ``source`` or ``target`` is outside ``[0, n)``.
            ValueError: If the endpoints are equal or ``flow_limit`` is negative.

        Notes:
            - Repeated calls continue from the current residual network. Keep
              the same source and target while a nonzero flow is retained.
            - Adding edges between calls is supported. A saturated network
              returns zero additional flow until more flow becomes possible.
            - The algorithm builds level graphs using BFS and finds blocking flows using DFS
            - Current-edge optimization is used to avoid revisiting saturated edges

        Time Complexity:
            O(n^2 m)
        """
        if not 0 <= source < self.n or not 0 <= target < self.n:
            raise IndexError('vertex must be within [0, n)')
        if source == target:
            raise ValueError('source and target must be different')
        if flow_limit is not None and flow_limit < 0:
            raise ValueError('flow_limit must be non-negative')
        if flow_limit is None:
            flow_limit = self.flow_inf
        self._build_graph()
        flow = Capacity(0)
        while flow < flow_limit:
            level = self._bfs(source, target)
            if level[target] == -1:
                break
            work = self._start[:self.n]
            while flow < flow_limit:
                f = self._dfs(source, target, Capacity(flow_limit - flow), level, work)
                if f == 0:
                    break
                flow = Capacity(flow + f)

        self._sync_flow()
        edges: list[MaximumFlowEdge] = []
        for e in range(self.m):
            u, v, cap = self.edges[e]
            edges.append(MaximumFlowEdge(u, v, cap, self.flow[e]))
        return MaximumFlowResult(flow=flow, edges=edges)


class BipartiteMatching:
    """
    Bipartite matching solver using maximum flow.

    Solves the maximum bipartite matching problem by reducing it to a maximum flow problem.
    Given a bipartite graph with two sets of vertices (left and right), finds the maximum
    number of edges such that no two edges share a vertex.

    Attributes:
        n1: Number of vertices in the left partition
        n2: Number of vertices in the right partition
        mf: Internal MaximumFlow instance
        source: Super source vertex
        target: Super sink vertex

    Examples:
        >>> # Job assignment problem: assign workers to jobs
        >>> bm = BipartiteMatching(3, 3)  # 3 workers, 3 jobs
        >>> # Worker 0 can do jobs 0 and 1
        >>> bm.add_edge(0, 0)
        >>> bm.add_edge(0, 1)
        >>> # Worker 1 can do jobs 1 and 2
        >>> bm.add_edge(1, 1)
        >>> bm.add_edge(1, 2)
        >>> # Worker 2 can do job 0
        >>> bm.add_edge(2, 0)
        >>>
        >>> result = bm.solve()
        >>> assert result.weight == 3  # Assign workers to jobs 1, 2, and 0.
        >>> assert result.success == True
        >>> # result.edges contains pairs (worker, job)

    Args:
        n1: Integer parameter ``n1``.
        n2: Integer parameter ``n2``.

    Complexity Notation:
        n1: Number of vertices in the left partition.
        n2: Number of vertices in the right partition.
        m: Number of bipartite edges added with ``add_edge``.

    Space Complexity:
        O(n1 + n2 + m)
    """
    def __init__(self, n1: int, n2: int) -> None:
        """Initialize a bipartite matching solver.

        Args:
            n1: Number of vertices in the left partition (0-indexed: 0 to n1-1)
            n2: Number of vertices in the right partition (0-indexed: 0 to n2-1)

        Returns:
            None.

        Raises:
            ValueError: If either partition size is negative.

        Time Complexity:
            O(n1 + n2)
        """
        if n1 < 0 or n2 < 0:
            raise ValueError('partition sizes must be non-negative')
        self.n1 = n1
        self.n2 = n2
        self.mf = MaximumFlow(n1 + n2 + 2)
        self.source = Node(n1 + n2)
        self.target = Node(n1 + n2 + 1)
        for i in range(n1):
            self.mf.add_edge(self.source, Node(i), Capacity(1))
        for i in range(n2):
            self.mf.add_edge(Node(n1 + i), self.target, Capacity(1))

    def add_edge(self, u: Node, v: Node) -> None:
        """
        Add an edge from left vertex u to right vertex v.

        Args:
            u: Vertex in the left partition (0 ≤ u < n1)
            v: Vertex in the right partition (0 ≤ v < n2)

        Raises:
            IndexError: If an endpoint is outside its partition.

        Returns:
            ``None``.

        Notes:
            - All edges have implicit capacity 1 for matching
            - Multiple edges between the same vertices are allowed but only one will be used

        Time Complexity:
            O(1)
        """
        if not 0 <= u < self.n1 or not 0 <= v < self.n2:
            raise IndexError('vertex must be within its partition')
        self.mf.add_edge(u, Node(self.n1 + v), Capacity(1))

    def solve(self) -> MatchingSuccess:
        """
        Find the maximum bipartite matching.

        Returns:
            MatchingSuccess containing:
            - weight: Number of edges in the maximum matching
            - edges: List of (left_vertex, right_vertex) pairs in the matching
            - success: Always True (bipartite matching always has a valid result)

        Notes:
            - The matching has maximum cardinality.
            - Each vertex appears in at most one edge in the matching
            - The algorithm uses Dinic's maximum-flow algorithm.
            - Edges are ``(left_vertex, right_vertex)`` pairs in separate index spaces.
            - Repeated calls return the full matching. Edges may be added between calls.

        Time Complexity:
            O((n1 + n2)^2 (n1 + n2 + m))
        """
        result = self.mf.solve(self.source, self.target)
        matching: list[tuple[int, int]] = []
        for edge in result.edges:
            if edge.flow == 0 or edge.source == self.source or edge.target == self.target:
                continue
            left = int(edge.source)
            right = int(edge.target - self.n1)
            matching.append((left, right))
        return MatchingSuccess(weight=len(matching), edges=matching, success=True)


class MinimumCostBFlow:
    """
    Minimum cost b-flow solver using cost-scaling algorithm.

    Reference:
        yosupo, https://judge.yosupo.jp/submission/32518.

    Solves the minimum cost flow problem with lower and upper bounds on edge capacities
    and supply/demand constraints at vertices (b-flow problem). The b-flow problem finds
    a flow that satisfies all capacity and balance constraints while minimizing total cost.

    Given:
    - A directed graph with n vertices
    - Edges with lower/upper capacity bounds and costs
    - Supply/demand values b[v] for each vertex (excess values)

    Find a flow f that:
    - Satisfies capacity constraints: lower[e] ≤ f[e] ≤ upper[e]
    - Satisfies flow conservation: ∑(out-flow) - ∑(in-flow) = b[v] for each vertex
    - Minimizes total cost: ∑(f[e] * cost[e]) over all edges

    Attributes:
        n: Number of vertices in the flow network
        m: Number of edges added to the network
        edges: List of edge tuples (from, to, lower, upper, cost)
        excess: Supply/demand at each vertex (positive = supply, negative = demand)
        dual: Dual variables (potentials) for vertices
        flow: Current flow values for each edge
        cost: Cost per unit flow for each edge
        maxcost: Maximum absolute cost among all edges
        eps: Current epsilon value for epsilon-optimality

    Examples:
        >>> # Transportation problem: minimize shipping cost
        >>> mcf = MinimumCostBFlow(4)
        >>> # Two factories (0, 1) and two warehouses (2, 3)
        >>> mcf.add_excess(0, 10)  # Factory 0 produces 10 units
        >>> mcf.add_excess(1, 15)  # Factory 1 produces 15 units
        >>> mcf.add_excess(2, -12) # Warehouse 2 needs 12 units
        >>> mcf.add_excess(3, -13) # Warehouse 3 needs 13 units
        >>>
        >>> # Shipping routes with min/max capacity and cost per unit
        >>> mcf.add_edge(0, 2, 0, 20, 3)  # Factory 0 to Warehouse 2
        >>> mcf.add_edge(0, 3, 0, 20, 5)  # Factory 0 to Warehouse 3
        >>> mcf.add_edge(1, 2, 0, 20, 2)  # Factory 1 to Warehouse 2
        >>> mcf.add_edge(1, 3, 0, 20, 4)  # Factory 1 to Warehouse 3
        >>>
        >>> result = mcf.solve()
        >>> result.feasible
        True
        >>> result.cost
        86

    Args:
        n: Number of elements, vertices, or rows handled by the structure.

    Complexity Notation:
        n: Number of vertices.
        m: Number of edges added with ``add_edge``.

    Space Complexity:
        O(n + m)
    """
    def __init__(self, n: int) -> None:
        """Initialize a minimum cost b-flow solver.

        Args:
            n: Number of vertices in the flow network (0-indexed)

        Returns:
            None.

        Raises:
            ValueError: If n is negative.

        Time Complexity:
            O(n)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self.m = 0
        self.edges: list[tuple[Node, Node, Capacity, Capacity, Cost]] = []
        self.excess: list[Capacity] = [Capacity(0)] * n
        self.dual: list[Cost] = [Cost(0)] * n
        self.flow: list[Capacity] = []
        self.cost: list[Cost] = []
        self.maxcost = Cost(0)
        self._start: list[int] = [0] * (n + 1)
        self._to: list[int] = []
        self._edge_id: list[int] = []
        self._direction: list[int] = []
        self._lower: list[int] = []
        self._upper: list[int] = []

    def add_edge(self, fr: Node, to: Node, lower: Capacity, upper: Capacity, cost: Cost) -> None:
        """
        Add a directed edge with capacity bounds and cost to the flow network.

        Args:
            fr: Source vertex of the edge (0-indexed)
            to: Target vertex of the edge (0-indexed)
            lower: Lower bound on flow through this edge (can be negative)
            upper: Upper bound on flow through this edge (can be negative)
            cost: Cost per unit of flow through this edge

        Returns:
            None.

        Notes:
            - Both lower and upper bounds can be negative
            - The edge allows flow in range [lower, upper] with cost per unit
            - The algorithm tracks the maximum absolute cost for epsilon initialization

        Time Complexity:
            O(1)
        """
        self.maxcost = max(self.maxcost, cost, -cost)
        self.edges.append((fr, to, lower, upper, cost))
        self.m += 1

    def add_excess(self, v: Node, x: Capacity) -> None:
        """
        Add supply/demand to a vertex.

        Args:
            v: Vertex index (0-indexed)
            x: Amount to add to vertex's excess (positive = supply, negative = demand)

        Returns:
            None.

        Notes:
            - Positive excess represents supply (source of flow)
            - Negative excess represents demand (sink of flow)
            - Multiple calls accumulate (add to existing excess)
            - The sum of all excesses must be zero for a feasible solution

        Time Complexity:
            O(1)
        """
        self.excess[v] = Capacity(self.excess[v] + x)

    def solve(self) -> MinimumCostBFlowResult:
        """
        Solve the minimum cost b-flow problem.

        Returns:
            MinimumCostBFlowResult containing:
            - feasible: True if a feasible flow exists, False otherwise
            - cost: Minimum cost of the flow if feasible, 0 otherwise
            - edges: List of all edges with their flow values

        Algorithm:
            1. First checks feasibility by reducing to maximum flow problem
            2. If feasible, applies cost-scaling algorithm with epsilon refinement
            3. Computes optimal dual variables (vertex potentials) for optimality

        Notes:
            - Returns infeasible if:
              - Sum of excesses is not zero
              - No flow satisfying all constraints exists
              - Any edge has upper < lower
            - Each call solves from scratch using the currently registered edges
              and excesses. Further edges or excesses may be added between calls.
            - Registered excesses are not changed by solving.
            - The algorithm maintains epsilon-optimality throughout refinement
            - Final solution is exactly optimal when epsilon reaches 1

        Time Complexity:
            Dominated by feasibility max-flow computation and repeated
            refinement phases.
        """
        self.flow = []
        self.cost = []
        self.dual = [Cost(0)] * self.n
        self.eps = 0
        excess = self.excess.copy()
        invalid_bounds = False
        mf = MaximumFlow(self.n + 2)
        sv = Node(self.n)
        tv = Node(self.n + 1)
        for fr, to, lower, upper, cost in self.edges:
            if upper < lower:
                invalid_bounds = True
                break
            excess[to] = Capacity(excess[to] + lower)
            excess[fr] = Capacity(excess[fr] - lower)
            mf.add_edge(fr, to, Capacity(upper - lower))
        excess_s_sum = excess_t_sum = Capacity(0)
        for i in range(self.n):
            if excess[i] > 0:
                excess_s_sum = Capacity(excess_s_sum + excess[i])
                mf.add_edge(sv, Node(i), excess[i])
            if excess[i] < 0:
                excess_t_sum = Capacity(excess_t_sum - excess[i])
                mf.add_edge(Node(i), tv, Capacity(-excess[i]))
        if invalid_bounds or excess_s_sum != excess_t_sum or mf.solve(sv, tv).flow != excess_s_sum:
            edges: list[MinimumCostBFlowEdge] = []
            for i in range(self.m):
                fr, to, lower, upper, cost = self.edges[i]
                edges.append(MinimumCostBFlowEdge(fr, to, lower, upper, cost, Capacity(0)))
            return MinimumCostBFlowResult(feasible=False, cost=Cost(0), edges=edges)

        for i in range(self.m):
            fr, to, cap, flow = mf.get_edge(EdgeNum(i))
            _, _, lower, upper, cost = self.edges[i]
            self.flow.append(Capacity(flow))
            self.cost.append(Cost(cost))
        self._build_graph()

        self.eps = self.maxcost * (self.n + 1)
        while self.eps > 1:
            self.eps = max(self.eps >> 2, 1)
            self._refine()

        res = Cost(0)
        for i in range(self.m):
            fr, to, lower, upper, _ = self.edges[i]
            cost = self.cost[i]
            res = Cost(res + (self.flow[i] + lower) * cost)

        while True:
            update = False
            start = self._start
            to = self._to
            edge_id = self._edge_id
            direction = self._direction
            lower_list = self._lower
            upper_list = self._upper
            flow = self.flow
            cost_list = self.cost
            dual = self.dual
            for v in range(self.n):
                for i in range(start[v], start[v + 1]):
                    c = to[i]
                    e = edge_id[i]
                    if direction[i] == 1:
                        cap = upper_list[e] - lower_list[e] - flow[e]
                        cost = cost_list[e] + dual[v]
                    else:
                        cap = flow[e]
                        cost = -cost_list[e] + dual[v]
                    if cap == 0:
                        continue
                    if cost < dual[c]:
                        dual[c] = Cost(cost)
                        update = True
            if not update:
                break

        edges: list[MinimumCostBFlowEdge] = []

        for i in range(self.m):
            fr, to, lower, upper, cost = self.edges[i]
            self.flow[i] = Capacity(self.flow[i] + lower)
            edges.append(MinimumCostBFlowEdge(fr, to, lower, upper, cost, self.flow[i]))

        return MinimumCostBFlowResult(feasible=True, cost=res, edges=edges)

    def _build_graph(self) -> None:
        degree = [0] * self.n
        lower_list = [0] * self.m
        upper_list = [0] * self.m
        for e, (fr, to, lower, upper, _) in enumerate(self.edges):
            fr_i = int(fr)
            to_i = int(to)
            lower_list[e] = int(lower)
            upper_list[e] = int(upper)
            degree[fr_i] += 1
            degree[to_i] += 1

        start = [0] * (self.n + 1)
        for i in range(self.n):
            start[i + 1] = start[i] + degree[i]

        arc_count = start[self.n]
        to = [0] * arc_count
        edge_id = [0] * arc_count
        direction = [0] * arc_count
        cursor = start[:]

        for e, (fr, to_node, _, _, _) in enumerate(self.edges):
            fr_i = int(fr)
            to_i = int(to_node)

            p = cursor[fr_i]
            cursor[fr_i] += 1
            to[p] = to_i
            edge_id[p] = e
            direction[p] = 1

            q = cursor[to_i]
            cursor[to_i] += 1
            to[q] = fr_i
            edge_id[q] = e
            direction[q] = -1

        self._start = start
        self._to = to
        self._edge_id = edge_id
        self._direction = direction
        self._lower = lower_list
        self._upper = upper_list

    def _refine(self) -> None:
        """
        Refine the current epsilon-optimal solution.

        This method performs one iteration of the cost-scaling algorithm by:
        1. Pushing flow along negative reduced cost edges to achieve epsilon-optimality
        2. Using a queue-based approach to handle excess flow at vertices
        3. Adjusting dual variables (potentials) when vertices have remaining excess

        The refinement maintains the invariant that all edges satisfy epsilon-optimality:
        For each edge (u,v) with positive residual capacity, the reduced cost
        c'(u,v) = c(u,v) + dual[u] - dual[v] ≥ -epsilon

        After refinement, epsilon is updated to the maximum violation of optimality
        conditions, preparing for the next scaling phase.

        Time Complexity:
            ``O(m sqrt(n))`` amortized for one cost-scaling refinement phase.
            Across ``solve()``, the refinement phases contribute
            ``O(m sqrt(n) log(nC))`` where ``C`` is the maximum absolute edge
            cost.
        """
        start = self._start
        to = self._to
        edge_id = self._edge_id
        direction = self._direction
        lower = self._lower
        upper = self._upper
        flow = self.flow
        cost_list = self.cost
        dual = self.dual
        scale = self.n + 1

        excess = [Capacity(0)] * self.n
        for v in range(self.n):
            for i in range(start[v], start[v + 1]):
                c = to[i]
                e = edge_id[i]
                if direction[i] == 1:
                    cap = upper[e] - lower[e] - flow[e]
                    cost = cost_list[e] * scale
                else:
                    cap = flow[e]
                    cost = -cost_list[e] * scale
                if cap != 0 and cost + dual[v] - dual[c] < 0:
                    excess[v] = Capacity(excess[v] - cap)
                    excess[c] = Capacity(excess[c] + cap)

                    if direction[i] == 1:
                        flow[e] = Capacity(flow[e] + cap)
                    else:
                        flow[e] = Capacity(flow[e] - cap)

        que:  deque[int] = deque()
        in_que = [False] * self.n
        work = start[:self.n]
        for i in range(self.n):
            if excess[i] > 0:
                in_que[i] = True
                que.append(i)

        while que:
            v = que.popleft()
            in_que[v] = False
            for i in range(work[v], start[v + 1]):
                c = to[i]
                e = edge_id[i]
                if direction[i] == 1:
                    cap = upper[e] - lower[e] - flow[e]
                    cost = cost_list[e] * scale
                else:
                    cap = flow[e]
                    cost = -cost_list[e] * scale
                if cap != 0 and cost + dual[v] - dual[c] < 0:
                    cap = min(cap, excess[v])
                    excess[v] = Capacity(excess[v] - cap)
                    excess[c] = Capacity(excess[c] + cap)

                    if direction[i] == 1:
                        flow[e] = Capacity(flow[e] + cap)
                    else:
                        flow[e] = Capacity(flow[e] - cap)

                    if not in_que[c] and excess[c] > 0:
                        in_que[c] = True
                        que.append(c)
                    if excess[v] == 0:
                        work[v] = i
                        break
            else:
                work[v] = start[v + 1]

            if excess[v] > 0:
                work[v] = start[v]
                down = scale * self.maxcost
                for i in range(start[v], start[v + 1]):
                    c = to[i]
                    e = edge_id[i]
                    if direction[i] == 1:
                        cap = upper[e] - lower[e] - flow[e]
                        cost = cost_list[e] * scale
                    else:
                        cap = flow[e]
                        cost = -cost_list[e] * scale
                    if cap != 0:
                        down = min(down, self.eps + cost + dual[v] - dual[c])
                dual[v] = Cost(dual[v] - down)
                que.append(v)
                in_que[v] = True

        self.eps = 0
        for v in range(self.n):
            for i in range(start[v], start[v + 1]):
                c = to[i]
                e = edge_id[i]
                if direction[i] == 1:
                    cap = upper[e] - lower[e] - flow[e]
                    cost = cost_list[e] * scale
                else:
                    cap = flow[e]
                    cost = -cost_list[e] * scale
                if cap != 0:
                    self.eps = max(self.eps, -cost - dual[v] + dual[c])
