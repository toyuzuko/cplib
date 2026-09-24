#!/usr/bin/env python3

from __future__ import annotations

from heapq import heappop, heappush
from math import hypot
from typing import NamedTuple

from cplib.datastructure.dsu import DisjointSetUnion
from cplib.graph.base import EdgeNum, Node, Weight
from cplib.graph.core import Graph
from cplib.graph.shortest import warshall_floyd


def _simple_undirected_adjacency_bits(graph: Graph) -> list[int]:
    if graph.is_directed:
        raise ValueError('The graph must be undirected')
    adj = [0] * graph.n
    for u, v in graph.edges:
        if u == v:
            raise ValueError('Self-loops are not supported')
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    return adj


def _maximum_independent_set_bits(adj: list[int]) -> int:
    n = len(adj)
    memo: dict[int, int] = {0: 0}

    def solve(mask: int) -> int:
        cached = memo.get(mask)
        if cached is not None:
            return cached

        cur = mask
        forced = 0
        while True:
            m = cur
            found = False
            while m:
                bit = m & -m
                v = bit.bit_length() - 1
                neigh = adj[v] & cur
                if neigh.bit_count() <= 1:
                    forced |= bit
                    cur &= ~bit
                    cur &= ~neigh
                    found = True
                    break
                m ^= bit
            if not found:
                break

        if forced:
            ans = forced | solve(cur)
            memo[mask] = ans
            return ans

        best_v = -1
        best_deg = -1
        m = cur
        while m:
            bit = m & -m
            v = bit.bit_length() - 1
            deg = (adj[v] & cur).bit_count()
            if deg > best_deg:
                best_v = v
                best_deg = deg
            m ^= bit

        bit = 1 << best_v
        without_v = solve(cur ^ bit)
        with_v = bit | solve(cur & ~bit & ~adj[best_v])
        ans = with_v if with_v.bit_count() >= without_v.bit_count() else without_v
        memo[mask] = ans
        return ans

    return solve((1 << n) - 1)


def maximum_independent_set(graph: Graph) -> list[Node]:
    """
    Find one maximum independent set of a simple undirected graph.

    Args:
        graph: Simple undirected input graph.

    Returns:
        Vertices in one maximum independent set.

    Raises:
        ValueError: If ``graph`` is directed or contains a self-loop.

    Time Complexity:
        Exponential in ``n`` in the worst case.

    Space Complexity:
        Exponential in ``n`` in the worst case.
    """
    adj = _simple_undirected_adjacency_bits(graph)
    mask = _maximum_independent_set_bits(adj)
    return [Node(v) for v in range(graph.n) if (mask >> v) & 1]


def maximum_clique(graph: Graph) -> list[Node]:
    """
    Find one maximum clique of a simple undirected graph.

    Args:
        graph: Simple undirected input graph.

    Returns:
        Vertices in one maximum clique.

    Raises:
        ValueError: If ``graph`` is directed or contains a self-loop.

    Time Complexity:
        Exponential in ``n`` in the worst case.

    Space Complexity:
        Exponential in ``n`` in the worst case.
    """
    adj = _simple_undirected_adjacency_bits(graph)
    full = (1 << graph.n) - 1
    complement = [(full ^ (1 << v)) & ~adj[v] for v in range(graph.n)]
    mask = _maximum_independent_set_bits(complement)
    return [Node(v) for v in range(graph.n) if (mask >> v) & 1]


def minimum_vertex_cover(graph: Graph) -> list[Node]:
    """
    Find one minimum vertex cover of a simple undirected graph.

    Args:
        graph: Simple undirected input graph.

    Returns:
        Vertices in one minimum vertex cover.

    Raises:
        ValueError: If ``graph`` is directed or contains a self-loop.

    Time Complexity:
        Exponential in ``n`` in the worst case.

    Space Complexity:
        Exponential in ``n`` in the worst case.
    """
    adj = _simple_undirected_adjacency_bits(graph)
    independent = _maximum_independent_set_bits(adj)
    return [Node(v) for v in range(graph.n) if not ((independent >> v) & 1)]


def bounded_vertex_cover(graph: Graph, k: int) -> list[Node] | None:
    """
    Find a vertex cover of size at most ``k`` by bounded search tree.

    Args:
        graph: Undirected input graph.
        k: Maximum allowed cover size.

    Returns:
        Vertices in one cover of size at most ``k``, or ``None`` if no such
        cover exists.

    Raises:
        ValueError: If ``graph`` is directed or ``k`` is negative.

    Time Complexity:
        O(2^k n m) in the worst case.

    Space Complexity:
        O(2^k + n + m)
    """
    if graph.is_directed:
        raise ValueError('The graph must be undirected')
    if k < 0:
        raise ValueError('k must be non-negative')

    n = graph.n
    edges = [(int(u), int(v)) for u, v in graph.edges]
    incident = [0] * n
    for i, (u, v) in enumerate(edges):
        bit = 1 << i
        incident[u] |= bit
        incident[v] |= bit

    failed: set[tuple[int, int]] = set()

    def force_reductions(edge_mask: int, remaining: int, chosen: int) -> tuple[int, int, int] | None:
        while True:
            if remaining < 0:
                return None
            forced_v = -1
            m = edge_mask
            while m:
                edge_bit = m & -m
                ei = edge_bit.bit_length() - 1
                u, v = edges[ei]
                if u == v:
                    forced_v = u
                    break
                m ^= edge_bit
            if forced_v == -1:
                for v in range(n):
                    neighbor_mask = 0
                    em = incident[v] & edge_mask
                    while em:
                        edge_bit = em & -em
                        ei = edge_bit.bit_length() - 1
                        a, b = edges[ei]
                        neighbor_mask |= 1 << (b if a == v else a)
                        em ^= edge_bit
                    if neighbor_mask.bit_count() > remaining:
                        forced_v = v
                        break
            if forced_v == -1:
                return edge_mask, remaining, chosen
            bit = 1 << forced_v
            if not (chosen & bit):
                chosen |= bit
                remaining -= 1
            edge_mask &= ~incident[forced_v]

    def search(edge_mask: int, remaining: int, chosen: int) -> int | None:
        reduced = force_reductions(edge_mask, remaining, chosen)
        if reduced is None:
            return None
        edge_mask, remaining, chosen = reduced
        if edge_mask == 0:
            return chosen
        if remaining == 0:
            return None
        state = (edge_mask, remaining)
        if state in failed:
            return None

        edge_bit = edge_mask & -edge_mask
        ei = edge_bit.bit_length() - 1
        u, v = edges[ei]
        for x in (u, v):
            bit = 1 << x
            next_chosen = chosen | bit
            next_remaining = remaining - (0 if chosen & bit else 1)
            result = search(edge_mask & ~incident[x], next_remaining, next_chosen)
            if result is not None:
                return result

        failed.add(state)
        return None

    cover = search((1 << len(edges)) - 1, k, 0)
    if cover is None:
        return None
    return [Node(v) for v in range(n) if (cover >> v) & 1]


class MinimumSteinerTreeResult(NamedTuple):
    """
    Result of a minimum Steiner tree query.

    Attributes:
        edges: Edge indices used by one optimal Steiner tree.
        weight: Total weight of that tree.

    Non-terminal Steiner vertices are implicit in the chosen edges.
    The returned edges form a connected subgraph spanning all terminals.
    Any one optimal Steiner tree may be returned.

    Space Complexity:
        - ``O(e)``, where ``e`` is the number of reported edges.
    """

    edges: list[EdgeNum]
    weight: Weight


def minimum_steiner_tree(graph: Graph, terminals: list[Node]) -> MinimumSteinerTreeResult:
    """
    Find the minimum Steiner tree connecting all terminal vertices.

    Args:
        graph: Weighted graph without negative edges.
        terminals: Terminal vertices that must be connected.

    Returns:
        MinimumSteinerTreeResult: Edge set and total weight of one optimal
        Steiner tree.

    Raises:
        ValueError: If negative edges exist or some terminals are disconnected.

    Time Complexity:
        - ``O(3^k n + 2^k m log n)``, where ``k = len(terminals)``

    Space Complexity:
        - ``O(2^k n)``
    """

    if graph.has_negative_edge:
        raise ValueError('minimum_steiner_tree does not support negative edge weights')
    k = len(terminals)
    n = graph.n
    if k == 1:
        return MinimumSteinerTreeResult(edges=[], weight=Weight(0))
    dp: list[list[int]] = [[Graph.dst_inf] * n for _ in range(1 << k)]
    pre_v = [[-1] * n for _ in range(1 << k)]
    pre_e = [[-1] * n for _ in range(1 << k)]
    for i, t in enumerate(terminals):
        dp[1 << i][t] = Weight(0)
    for s in range(1, 1 << k):
        for v in range(n):
            ns = s
            while True:
                if dp[ns][v] != Graph.dst_inf and dp[s ^ ns][v] != Graph.dst_inf:
                    nxt = min(dp[s][v], dp[ns][v] + dp[s ^ ns][v])
                    if nxt < dp[s][v]:
                        dp[s][v] = nxt
                        pre_v[s][v] = ns
                if ns == 0:
                    break
                ns = (ns - 1) & s
        pq: list[tuple[int, Node]] = []
        for v in range(n):
            heappush(pq, (dp[s][v], Node(v)))
        while pq:
            d, u = heappop(pq)
            if dp[s][u] < d:
                continue
            for v, e in graph.graph[u]:
                if dp[s][v] > d + graph.wt[e]:
                    dp[s][v] = d + graph.wt[e]
                    pre_v[s][v] = u
                    pre_e[s][v] = e
                    heappush(pq, (dp[s][v], v))
    cost = dp[(1 << k) - 1][terminals[0]]
    if cost == Graph.dst_inf:
        raise ValueError('Some terminal nodes are not connected')
    st = [((1 << k) - 1, terminals[0])]
    tree: list[EdgeNum] = []
    dsu = DisjointSetUnion(n)
    visited: set[tuple[int, Node]] = set()
    while st:
        x, y = st.pop()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        if pre_e[x][y] == -1:
            if pre_v[x][y] != -1:
                st.append((pre_v[x][y], y))
                st.append((x ^ pre_v[x][y], y))
        else:
            e = EdgeNum(pre_e[x][y])
            # Overlapping optimal subtrees can share zero-weight edges or cycles.
            if dsu.merge(*graph.edges[e]):
                tree.append(e)
            st.append((x, Node(pre_v[x][y])))
    return MinimumSteinerTreeResult(edges=tree, weight=Weight(cost))


def undirected_chinese_postman_problem(graph: Graph) -> Weight:
    """
    Return the shortest closed walk length that traverses every edge.

    Isolated vertices are ignored. All vertices incident to at least one edge
    must belong to the same connected component.

    Args:
        graph: Undirected graph with non-negative edge weights.

    Returns:
        Minimum total length of a closed walk containing every edge at least
        once.

    Raises:
        ValueError: If ``graph`` is directed, contains a negative edge, or has
            edges in multiple connected components.

    Time Complexity:
        O(n^3 + k^2 2^k), where ``k`` is the number of odd-degree vertices.

    Space Complexity:
        O(n^2 + 2^k)
    """
    if graph.is_directed:
        raise ValueError('The graph must be undirected')
    if graph.has_negative_edge:
        raise ValueError('undirected_chinese_postman_problem does not support negative edge weights')
    if graph.m == 0:
        return Weight(0)

    dist = warshall_floyd(graph)
    start = next(v for v in range(graph.n) if graph.deg[v] > 0)
    for v in range(graph.n):
        if graph.deg[v] > 0 and dist[start][v] == Graph.dst_inf:
            raise ValueError('All non-isolated vertices must be connected')

    total = Weight(sum(graph.wt))
    odd = [v for v in range(graph.n) if graph.deg[v] & 1]
    k = len(odd)
    if k == 0:
        return total

    inf = Graph.dst_inf
    dp = [inf] * (1 << k)
    dp[0] = Weight(0)
    full = (1 << k) - 1
    for mask in range(full):
        if dp[mask] == inf:
            continue
        i = 0
        while (mask >> i) & 1:
            i += 1
        for j in range(i + 1, k):
            if (mask >> j) & 1:
                continue
            next_mask = mask | (1 << i) | (1 << j)
            cand = Weight(dp[mask] + dist[odd[i]][odd[j]])
            if cand < dp[next_mask]:
                dp[next_mask] = cand
    return Weight(total + dp[full])


def bitonic_tsp(points: list[tuple[float, float]]) -> float:
    """
    Return the length of a shortest bitonic tour through planar points.

    The points must be sorted by increasing x-coordinate. A bitonic tour starts
    at the leftmost point, moves monotonically to the rightmost point along one
    chain, then returns monotonically to the leftmost point along the other
    chain while visiting every point exactly once.

    Args:
        points: Points sorted by increasing x-coordinate.

    Returns:
        Minimum bitonic tour length.

    Raises:
        ValueError: If fewer than two points are given or x-coordinates are not
            strictly increasing.

    Time Complexity:
        O(n^2), where ``n`` is ``len(points)``.

    Space Complexity:
        O(n^2)
    """
    n = len(points)
    if n < 2:
        raise ValueError('at least two points are required')
    for i in range(n - 1):
        if points[i][0] >= points[i + 1][0]:
            raise ValueError('points must be sorted by strictly increasing x-coordinate')

    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = points[i]
        for j in range(i + 1, n):
            xj, yj = points[j]
            d = hypot(xi - xj, yi - yj)
            dist[i][j] = d
            dist[j][i] = d

    inf = float('inf')
    dp = [[inf] * n for _ in range(n)]
    dp[0][1] = dist[0][1]
    for j in range(1, n - 1):
        for i in range(j):
            cur = dp[i][j]
            if cur == inf:
                continue
            if cur + dist[j][j + 1] < dp[i][j + 1]:
                dp[i][j + 1] = cur + dist[j][j + 1]
            cand = cur + dist[i][j + 1]
            if cand < dp[j][j + 1]:
                dp[j][j + 1] = cand
    return dp[n - 2][n - 1] + dist[n - 2][n - 1]


class TravelingSalesmanResult(NamedTuple):
    """
    Result of one traveling salesman query.

    Attributes:
        path: One optimal Hamiltonian tour represented by visited vertices.
        weight: Total weight of that tour.

    The tour is reported in traversal order starting from vertex ``0``.
    The closing edge back to ``0`` is included only in ``weight``.
    Any one optimal Hamiltonian tour may be returned.

    Space Complexity:
        - ``O(n)``
    """

    path: list[Node]
    weight: Weight


def traveling_salesman_problem(graph: Graph) -> TravelingSalesmanResult:
    """
    Solve the traveling salesman problem starting and ending at vertex ``0``.

    Sparse and dense graphs are both supported. Parallel edges are merged by
    minimum weight; self-loops are ignored. A single vertex has a zero-cost tour.

    Args:
        graph: Directed or undirected weighted graph. Finite partial-tour
            and tour costs must lie strictly between ``-Graph.dst_inf`` and
            ``Graph.dst_inf``.

    Returns:
        TravelingSalesmanResult: One minimum tour and its total weight.

    Raises:
        ValueError: If the graph is empty or no Hamiltonian tour exists.

    Time Complexity:
        - ``O(m + n^2 2^n)``

    Space Complexity:
        - ``O(n 2^n)``
    """

    n = graph.n
    if n == 0:
        raise ValueError('The graph must contain at least one vertex')
    if n == 1:
        return TravelingSalesmanResult(path=[Node(0)], weight=Weight(0))
    inf = Graph.dst_inf
    costs = [[inf] * n for _ in range(n)]
    for e, (u, v) in enumerate(graph.edges):
        costs[u][v] = min(costs[u][v], graph.wt[e])
        if not graph.is_directed:
            costs[v][u] = min(costs[v][u], graph.wt[e])
    full = (1 << n) - 1
    dp: list[list[int]] = [[inf] * n for _ in range(1 << n)]
    dp[1][0] = 0
    for s in range(1, 1 << n, 2):
        for u in range(n):
            if dp[s][u] == inf:
                continue
            remaining = full ^ s
            while remaining:
                bit = remaining & -remaining
                v = bit.bit_length() - 1
                remaining ^= bit
                if costs[u][v] != inf:
                    nxt = s | bit
                    dp[nxt][v] = min(dp[nxt][v], dp[s][u] + costs[u][v])
    cost = inf
    end = -1
    for u in range(1, n):
        if dp[full][u] != inf and costs[u][0] != inf:
            candidate = dp[full][u] + costs[u][0]
            if candidate < cost:
                cost = Weight(candidate)
                end = u
    if end == -1:
        raise ValueError('No Hamiltonian tour exists')
    path: list[Node] = []
    s = full
    u = end
    while s != 1:
        path.append(Node(u))
        previous = s ^ (1 << u)
        for v in range(n):
            if previous >> v & 1 and dp[previous][v] != inf and costs[v][u] != inf:
                if dp[s][u] == dp[previous][v] + costs[v][u]:
                    s = previous
                    u = v
                    break
    path.append(Node(0))
    path.reverse()
    return TravelingSalesmanResult(path=path, weight=cost)
