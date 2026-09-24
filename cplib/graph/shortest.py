#!/usr/bin/env python3

"""Shortest paths with integer distance sentinels.

Finite distances and intermediate finite path sums must lie strictly between
``-Graph.dst_inf`` and ``Graph.dst_inf``. The endpoints of this range are
reserved for negative-cycle influence and unreachable vertices, respectively.
``simplify_graph`` only transforms edges and has no such weight restriction.
"""

from __future__ import annotations

from collections import deque
from heapq import heappop, heappush
from typing import NamedTuple

from cplib.datastructure.queue import RadixHeap
from cplib.graph.base import Node, Weight
from cplib.graph.core import Graph


def dijkstra_with_prev(graph: Graph, source: Node) -> tuple[list[Weight], list[Node]]:
    """
    Run Dijkstra's algorithm and keep predecessor information.

    Args:
        graph: Weighted graph with non-negative edge weights.
        source: Source vertex.

    Returns:
        tuple[list[Weight], list[Node]]: Distances and predecessor tree.

    Raises:
        ValueError: If ``graph`` contains a negative edge.

    Time Complexity:
        - ``O((n + m) log n)``

    Space Complexity:
        - ``O(n + m)`` auxiliary space, including queued distance candidates.
    """
    if graph.has_negative_edge:
        raise ValueError('Dijkstra does not work with negative edge weights')
    dst = [Graph.dst_inf] * graph.n
    prev = [Node(-1)] * graph.n
    dst[source] = Weight(0)
    heap: list[int] = [int(source)]
    while heap:
        d, u = divmod(heappop(heap), graph.n)
        d, u = Weight(d), Node(u)
        if d > dst[u]:
            continue
        for v, i in graph.graph[u]:
            if dst[u] + graph.wt[i] < dst[v]:
                dst[v] = Weight(dst[u] + graph.wt[i])
                prev[v] = u
                heappush(heap, int(dst[v] * graph.n + v))
    return dst, prev


def radix_dijkstra_with_prev(graph: Graph, source: Node) -> tuple[list[Weight], list[Node]]:
    """
    Run Dijkstra's algorithm with a radix heap.

    Edge weights must be non-negative integers. Compared with the binary heap
    version, this can be faster when shortest path distances stay within a
    practical integer range.

    Args:
        graph: Weighted graph with non-negative integer edge weights.
        source: Source vertex.

    Returns:
        tuple[list[Weight], list[Node]]: Distances and predecessor tree.

    Raises:
        ValueError: If ``graph`` contains a negative edge.

    Time Complexity:
        O((n + m) log C), where ``C`` is the maximum shortest-path distance.

    Space Complexity:
        O(n + m)
    """
    if graph.has_negative_edge:
        raise ValueError('Radix-heap Dijkstra does not work with negative edge weights')
    dst = [Graph.dst_inf] * graph.n
    prev = [Node(-1)] * graph.n
    dst[source] = Weight(0)
    heap = RadixHeap[Node]()
    heap.push(0, source)
    while heap:
        d, u = heap.pop()
        if d > dst[u]:
            continue
        for v, i in graph.graph[u]:
            nd = d + graph.wt[i]
            if nd < dst[v]:
                dst[v] = Weight(nd)
                prev[v] = u
                heap.push(nd, v)
    return dst, prev


def _bfs(graph: Graph, source: Node) -> tuple[list[Weight], list[Node]]:
    """
    Run BFS treating every edge as cost ``1``.

    Edge weights are ignored even when ``graph`` stores weighted edges.

    Args:
        graph: Input graph.
        source: Source vertex.

    Returns:
        Distances in number of edges and predecessor tree.

    Time Complexity:
        - ``O(n + m)``
    """
    dst = [Graph.dst_inf] * graph.n
    prev = [Node(-1)] * graph.n
    dst[source] = Weight(0)
    q = deque([source])
    while q:
        u = q.popleft()
        for v, _ in graph.graph[u]:
            if dst[u] + 1 < dst[v]:
                dst[v] = Weight(dst[u] + 1)
                prev[v] = u
                q.append(v)
    return dst, prev


def _bellman_ford(graph: Graph, source: Node) -> tuple[list[Weight], list[Node]]:
    dst = [Graph.dst_inf] * graph.n
    prev = [Node(-1)] * graph.n
    dst[source] = Weight(0)

    for _ in range(graph.n - 1):
        updated = False
        for u in range(graph.n):
            if dst[u] == Graph.dst_inf:
                continue
            for v, i in graph.graph[u]:
                if dst[u] + graph.wt[i] < dst[v]:
                    dst[v] = Weight(dst[u] + graph.wt[i])
                    prev[v] = Node(u)
                    updated = True
        if not updated:
            break

    for u in range(graph.n):
        if dst[u] == Graph.dst_inf:
            continue
        for v, i in graph.graph[u]:
            if dst[u] + graph.wt[i] < dst[v]:
                visited = [False] * graph.n
                q = deque([v])
                while q:
                    w = q.popleft()
                    if visited[w]:
                        continue
                    visited[w] = True
                    dst[w] = Weight(-Graph.dst_inf)
                    for x, _ in graph.graph[w]:
                        if not visited[x]:
                            q.append(x)

    return dst, prev


def simplify_graph(graph: Graph) -> Graph:
    """
    Remove self-loops and merge parallel edges by minimum weight.

    Args:
        graph: Input graph.

    Returns:
        Graph: Simplified graph on the same vertex set.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(m)``
    """
    seen_edges: dict[int, Weight] = {}
    new_graph = Graph(
        graph.n,
        is_directed=graph.is_directed,
        connectivity_check=graph.connectivity_check,
    )
    for u in range(graph.n):
        for v, e in graph.graph[u]:
            if u == v:
                continue
            if not graph.is_directed and u > v:
                continue
            key = u * graph.n + v
            seen_edges[key] = min(seen_edges.get(key, graph.wt[e]), graph.wt[e])
    for uv in seen_edges:
        u, v = divmod(uv, graph.n)
        new_graph.add_edge(Node(u), Node(v), seen_edges[uv])
    return new_graph


def dijkstra(graph: Graph, source: Node) -> list[Weight]:
    """
    Return shortest distances from ``source`` using Dijkstra's algorithm.

    Args:
        graph: Graph with non-negative edge weights.
        source: Source vertex.

    Returns:
        list[Weight]: Distance from ``source`` to every vertex.

    Raises:
        ValueError: If ``graph`` contains a negative edge.

    Time Complexity:
        O((n + m) log n)
    Space Complexity:
        O(n + m), including queued distance candidates.
    """

    return dijkstra_with_prev(graph, source)[0]


def radix_dijkstra(graph: Graph, source: Node) -> list[Weight]:
    """
    Return shortest distances from ``source`` using radix-heap Dijkstra.

    Args:
        graph: Graph with non-negative integer edge weights.
        source: Source vertex.

    Returns:
        list[Weight]: Distance from ``source`` to every vertex.

    Raises:
        ValueError: If ``graph`` contains a negative edge.

    Time Complexity:
        O((n + m) log C), where ``C`` is the maximum shortest-path distance.

    Space Complexity:
        O(n + m)
    """
    return radix_dijkstra_with_prev(graph, source)[0]


def bfs(graph: Graph, source: Node) -> list[Weight]:
    """
    Return shortest distances from ``source`` in an unweighted graph.

    Every edge is treated as cost ``1``; stored edge weights are ignored.

    Args:
        graph: Graph whose edges are interpreted as unit cost.
        source: Source vertex.

    Returns:
        list[Weight]: Distance from ``source`` to every vertex.

    Time Complexity:
        O(n + m)
    Space Complexity:
        O(n)
    """

    return _bfs(graph, source)[0]


def bellman_ford(graph: Graph, source: Node) -> list[Weight]:
    """
    Return shortest distances from ``source`` using Bellman-Ford.

    Vertices affected by a reachable negative cycle are marked with
    ``-Graph.dst_inf``.

    Args:
        graph: Input graph.
        source: Source vertex.

    Returns:
        list[Weight]: Distance from ``source`` to every vertex.

    Time Complexity:
        O(n m)

    Space Complexity:
        O(n)
    """
    return _bellman_ford(graph, source)[0]


class ShortestPathResult(NamedTuple):
    """
    Result of shortest path computation.

    Attributes:
        distance: Shortest distance from the source to the target.
        path: Vertices on one shortest path from source to target.

    The path includes both endpoints.
    It is one realizing shortest path, not necessarily unique.
    Distances use the same ``Weight`` type as the graph.

    Space Complexity:
        - ``O(k)``, where ``k`` is the path length.
    """

    distance: Weight
    path: list[Node]


def shortest_path(graph: Graph, source: Node, target: Node) -> ShortestPathResult:
    """
    Return one shortest path from ``source`` to ``target``.

    The function automatically chooses BFS, Dijkstra, or Bellman-Ford based on
    the graph flags.

    Args:
        graph: Input graph.
        source: Start vertex.
        target: Goal vertex.

    Returns:
        ShortestPathResult: Shortest distance and one realizing path.

    Raises:
        ValueError: If no path exists or the target is affected by a negative cycle.

    Time Complexity:
        Dominated by the selected single-source shortest-path algorithm
            - O(n + m) for BFS on unweighted graphs
            - O((n + m) log n) for Dijkstra on graphs with non-negative weights
            - O(n m) for Bellman-Ford on graphs with negative weights

    Space Complexity:
        O(n + m) with the binary heap, or O(n) with BFS or Bellman-Ford.
    """

    if not graph.is_weighted:
        dst, par = _bfs(graph, source)
    elif graph.has_negative_edge:
        dst, par = _bellman_ford(graph, source)
    else:
        dst, par = dijkstra_with_prev(graph, source)

    if dst[target] == Graph.dst_inf:
        raise ValueError('No path exists from the source to the target')
    if dst[target] == -Graph.dst_inf:
        raise ValueError('Target is affected by a negative cycle')

    path: list[Node] = []
    cur = target
    while cur != -1:
        path.append(cur)
        cur = par[cur]
    path.reverse()
    return ShortestPathResult(distance=dst[target], path=path)


def warshall_floyd(graph: Graph) -> list[list[Weight]]:
    """
    Return all-pairs shortest-path distances.

    Args:
        graph: Input graph.

    Returns:
        list[list[Weight]]: Matrix ``dist`` where ``dist[u][v]`` is the shortest
        distance from ``u`` to ``v``. Entries affected by a negative cycle are
        ``-Graph.dst_inf``; unreachable pairs are ``Graph.dst_inf``.

    Time Complexity:
        O(n^3)

    Space Complexity:
        O(n^2)
    """

    dist = [[Graph.dst_inf] * graph.n for _ in range(graph.n)]
    for i in range(graph.n):
        dist[i][i] = Weight(0)
    for i, (u, v) in enumerate(graph.edges):
        if dist[u][v] > graph.wt[i]:
            dist[u][v] = graph.wt[i]
        if not graph.is_directed and dist[v][u] > graph.wt[i]:
            dist[v][u] = graph.wt[i]

    for k in range(graph.n):
        for i in range(graph.n):
            for j in range(graph.n):
                if dist[i][k] != Graph.dst_inf and dist[k][j] != Graph.dst_inf:
                    if dist[i][j] > dist[i][k] + dist[k][j]:
                        dist[i][j] = Weight(dist[i][k] + dist[k][j])

    if graph.has_negative_edge:
        negative_vertices = [k for k in range(graph.n) if dist[k][k] < 0]
        for k in negative_vertices:
            for i in range(graph.n):
                if dist[i][k] == Graph.dst_inf:
                    continue
                for j in range(graph.n):
                    if dist[k][j] != Graph.dst_inf:
                        dist[i][j] = Weight(-Graph.dst_inf)

    return dist


def update_dist_matrix(dist_matrix: list[list[Weight]], u: Node, v: Node, w: Weight, is_directed: bool = True) -> None:
    """
    Update an all-pairs distance matrix after inserting one edge.

    Args:
        dist_matrix: Exact all-pairs shortest-path matrix of a graph without
            negative cycles. Use ``Graph.dst_inf`` for unreachable pairs.
        u: Start vertex of the new edge.
        v: End vertex of the new edge.
        w: Weight of the new edge, strictly between ``-Graph.dst_inf``
            and ``Graph.dst_inf``.
        is_directed: Whether the inserted edge is directed.

    Returns:
        ``None``. The matrix is updated in place. Finite old and new distances
        must lie strictly between ``-Graph.dst_inf`` and ``Graph.dst_inf``.

    Raises:
        ValueError: If the matrix already contains a negative cycle, the new
            edge creates one, or ``w`` is outside the supported range. The
            matrix is unchanged on these errors.

    Time Complexity:
        O(n^2) in the size of the processed input or stored data

    Space Complexity:
        in-place update of the provided distance matrix, so O(1) additional space
    """

    n = len(dist_matrix)
    if not -Graph.dst_inf < w < Graph.dst_inf:
        raise ValueError('edge weight must lie strictly between -Graph.dst_inf and Graph.dst_inf')
    if any(dist_matrix[i][i] < 0 for i in range(n)):
        raise ValueError('the distance matrix must not contain a negative cycle')
    if (is_directed and dist_matrix[v][u] != Graph.dst_inf and dist_matrix[v][u] + w < 0) or (not is_directed and w < 0):
        raise ValueError('the inserted edge would create a negative cycle')

    if is_directed:
        if dist_matrix[u][v] <= w:
            return
        dist_matrix[u][v] = w
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if dist_matrix[i][u] != Graph.dst_inf and dist_matrix[v][j] != Graph.dst_inf:
                    new_dist = Weight(dist_matrix[i][u] + w + dist_matrix[v][j])
                    if new_dist < dist_matrix[i][j]:
                        dist_matrix[i][j] = new_dist
    else:
        if dist_matrix[u][v] <= w:
            return
        dist_matrix[u][v] = w
        dist_matrix[v][u] = w
        for i in range(n):
            for j in range(i + 1, n):
                if dist_matrix[i][u] != Graph.dst_inf and dist_matrix[v][j] != Graph.dst_inf:
                    new_dist = Weight(dist_matrix[i][u] + w + dist_matrix[v][j])
                    if new_dist < dist_matrix[i][j]:
                        dist_matrix[i][j] = new_dist
                        dist_matrix[j][i] = new_dist
                if dist_matrix[i][v] != Graph.dst_inf and dist_matrix[u][j] != Graph.dst_inf:
                    new_dist = Weight(dist_matrix[i][v] + w + dist_matrix[u][j])
                    if new_dist < dist_matrix[i][j]:
                        dist_matrix[i][j] = new_dist
                        dist_matrix[j][i] = new_dist
