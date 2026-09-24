#!/usr/bin/env python3

from __future__ import annotations

from typing import NamedTuple

from cplib.datastructure.dsu import DisjointSetUnion, UndoableDSU
from cplib.datastructure.queue import OffsetPriorityQueue
from cplib.graph.base import EdgeNum, Node, Weight
from cplib.graph.core import Graph
from cplib.graph.shortest import dijkstra_with_prev


class MinimumSpanningTreeResult(NamedTuple):
    """
    Result of minimum spanning tree computation.

    Attributes:
        edges (list[EdgeNum]): a list of edge indices in the original graph that are included in the minimum spanning tree or arborescence.
                            The indices refer to the original graph; their order is unspecified.
        weight (Weight): the total weight of the edges included in the minimum spanning tree or arborescence.

    The result type is shared by both undirected and directed variants.

    Space Complexity:
        O(n)
    """

    edges: list[EdgeNum]
    weight: Weight


def minimum_spanning_tree(graph: Graph) -> MinimumSpanningTreeResult:
    """
    Find the minimum spanning tree using Kruskal's algorithm.

    Args:
        graph: An undirected graph.

    Returns:
        MinimumSpanningTreeResult containing:
            - edges: List of edge indices in the MST
            - weight: Total weight of the MST

    Raises:
        ValueError: If the graph is directed or not connected.

    Examples:
        >>> g = Graph(3)
        >>> g.add_edge(0, 1, 10)
        >>> g.add_edge(1, 2, 5)
        >>> g.add_edge(0, 2, 15)
        >>> result = minimum_spanning_tree(g)
        >>> print(result.weight)  # 15
        15

    Space Complexity:
        O(n + m)

    Time Complexity:
        O(m log m)
    """

    if graph.is_directed:
        raise ValueError('The graph must be undirected')
    wt_and_idx = [graph.wt[i] * graph.m + i for i, _ in enumerate(graph.edges)]
    wt_and_idx.sort()
    mst_edges: list[EdgeNum] = []
    mst_weight = 0
    dsu = DisjointSetUnion(graph.n)
    for wi in wt_and_idx:
        w, i = divmod(wi, graph.m)
        w = Weight(w)
        u, v = graph.edges[i]
        if dsu.merge(u, v):
            mst_edges.append(EdgeNum(i))
            mst_weight += w
    if len(mst_edges) != graph.n - 1:
        raise ValueError('The graph is not connected')
    return MinimumSpanningTreeResult(edges=mst_edges, weight=Weight(mst_weight))


def directed_minimum_spanning_tree(graph: Graph, root: Node) -> MinimumSpanningTreeResult:
    """
    Find the minimum spanning tree in a directed graph (minimum arborescence).

    Computes a directed spanning tree rooted at the given vertex with minimum
    total edge weight. Also known as minimum cost arborescence or minimum
    branching.

    Args:
        graph: A directed graph.
        root: Root vertex of the arborescence (0-indexed).

    Returns:
        MinimumSpanningTreeResult containing:
            - edges: List of edge indices in the minimum arborescence
            - weight: Total weight of the minimum arborescence

    Raises:
        ValueError: If the graph is undirected.
        ValueError: If no spanning tree exists from the given root.

    Space Complexity:
        O(n + m)

    Time Complexity:
        O((n + m) log n)
    """

    if not graph.is_directed:
        raise ValueError('The graph must be directed')
    n, m = graph.n, graph.m
    heaps = [OffsetPriorityQueue(ascending=True) for _ in range(n)]
    for u in range(n):
        for v, e in graph.graph[u]:
            heaps[v].push(graph.wt[e] * m + e)
    dsu = UndoableDSU(n)
    seen = [-1] * n
    seen[root] = root
    in_edge: list[tuple[int, int, int]] = [(-1, -1, -1)] * n
    cycs: list[tuple[int, int, list[tuple[int, int, int]]]] = []
    total_weight = 0
    for s in range(n):
        u = s
        stack: list[tuple[int, int, int, int]] = []
        while seen[u] < 0:
            if len(heaps[u]) == 0:
                raise ValueError('Given root does not lead to a spanning tree')
            seen[u] = s
            w, e = divmod(heaps[u].pop(), m)
            a, _ = graph.edges[e]
            total_weight += w
            heaps[u].add_offset(-w * m)
            stack.append((a, e, w, u))
            u = dsu.leader(a)
            if seen[u] == s:
                heap = OffsetPriorityQueue(ascending=True)
                snap = dsu.snapshot()
                comp: list[tuple[int, int, int]] = []
                while True:
                    ai, ei, wi, vi = stack.pop()
                    comp.append((ai, ei, wi))
                    heap.meld(heaps[vi])
                    if not dsu.merge(u, vi):
                        break
                u = dsu.leader(u)
                heaps[u] = heap
                seen[u] = -1
                cycs.append((u, snap, comp))
        for ai, ei, wi, _ in stack:
            _, bi = graph.edges[ei]
            in_edge[dsu.leader(bi)] = (ai, ei, wi)
    for u, snap, comp in cycs[::-1]:
        dsu.rollback(snap)
        a_sup, e_sup, w_sup = in_edge[u]
        for a, e, w in comp:
            _, b = graph.edges[e]
            in_edge[dsu.leader(b)] = (a, e, w)
        _, b_sup = graph.edges[e_sup]
        in_edge[dsu.leader(b_sup)] = (a_sup, e_sup, w_sup)
    mst_edges: list[EdgeNum] = []
    for v in range(graph.n):
        if v == root:
            continue
        _, e_idx, _ = in_edge[v]
        mst_edges.append(EdgeNum(e_idx))
    return MinimumSpanningTreeResult(edges=mst_edges, weight=Weight(total_weight))


class MinimumDiameterSpanningTreeResult(NamedTuple):
    """
    Result of a minimum-diameter spanning tree query.

    Attributes:
        edges: Edge indices of one spanning tree attaining the returned diameter.
        diameter: Diameter of that spanning tree.

    The edges use original graph indices; their order is unspecified.
    They form a spanning tree of the original graph.
    Any one optimal tree may be returned when multiple optima exist.

    Space Complexity:
        - ``O(n)``
    """

    edges: list[EdgeNum]
    diameter: Weight


def minimum_diameter_spanning_tree(graph: Graph) -> MinimumDiameterSpanningTreeResult:
    """
    Find a spanning tree with minimum possible diameter.

    Args:
        graph: Connected undirected graph with non-negative edge weights.

    Returns:
        MinimumDiameterSpanningTreeResult: Edge set of one optimal spanning tree
        and its diameter.

    Raises:
        ValueError: If ``graph`` is directed, disconnected, or has negative edges.

    Time Complexity:
        - Dominated by all-pairs Dijkstra: typically ``O(n m log n + n^3)``

    Space Complexity:
        - ``O(n^2)``
    """

    if graph.is_directed:
        raise ValueError('The graph must be undirected')
    if graph.has_negative_edge:
        raise ValueError('minimum_diameter_spanning_tree does not support negative edge weights')

    n = graph.n
    if n == 1:
        return MinimumDiameterSpanningTreeResult([], Weight(0))

    edge_id = [-1] * (n * n)
    for ei, (u, v) in enumerate(graph.edges):
        if edge_id[u * n + v] == -1 or graph.wt[ei] < graph.wt[edge_id[u * n + v]]:
            edge_id[u * n + v] = ei
        if edge_id[v * n + u] == -1 or graph.wt[ei] < graph.wt[edge_id[v * n + u]]:
            edge_id[v * n + u] = ei

    dist = [Graph.dst_inf] * (n * n)
    parent_edge = [-1] * (n * n)
    for s in range(n):
        ds, prev = dijkstra_with_prev(graph, Node(s))
        for v in range(n):
            dist[s * n + v] = ds[v]
            if ds[v] == Graph.dst_inf:
                raise ValueError(f'Node {v} and node {s} are not connected')
            if v != s and prev[v] != -1:
                parent_edge[s * n + v] = edge_id[prev[v] * n + v]

    best_vertex_diam = Graph.dst_inf
    best_vertex = -1
    best_edge_diam = Graph.dst_inf
    best_edge_info: tuple[int, list[int]] = (-1, [])

    for r in range(n):
        h = max(dist[r * n: r * n + n])
        diam = Weight(h * 2)
        if diam < best_vertex_diam:
            best_vertex = r
            best_vertex_diam = diam

    for ei, (u, v) in enumerate(graph.edges):
        if u == v:
            continue
        if graph.wt[ei] >= best_edge_diam or graph.wt[ei] >= best_vertex_diam:
            continue

        du = [dist[u * n + i] for i in range(n)]
        dv = [dist[v * n + i] for i in range(n)]
        sorted_idx = [i for i in range(n) if i != u and i != v]
        sorted_idx.sort(key=du.__getitem__)
        sorted_idx.sort(key=lambda i: du[i] - dv[i])

        prefix_max_du = [0] * (n - 1)
        for i in range(n - 2):
            prefix_max_du[i + 1] = max(prefix_max_du[i], du[sorted_idx[i]])

        suffix_max_dv = [0] * (n - 1)
        for i in range(n - 2)[::-1]:
            suffix_max_dv[i] = max(suffix_max_dv[i + 1], dv[sorted_idx[i]])

        for split in range(n - 1):
            maxdu = prefix_max_du[split]
            maxdv = suffix_max_dv[split]
            diam = max(
                Weight(maxdu * 2),
                Weight(maxdv * 2),
                Weight(maxdu + graph.wt[ei] + maxdv),
            )
            if diam < best_edge_diam:
                best_edge_diam = diam
                best_edge_info = (ei, [sorted_idx[i] for i in range(split)])

    edges: list[EdgeNum] = []
    if best_vertex_diam <= best_edge_diam:
        for v in range(n):
            if v == best_vertex:
                continue
            edges.append(EdgeNum(parent_edge[best_vertex * n + v]))
    else:
        ei, assign_u = best_edge_info
        u, v = graph.edges[ei]
        assign_u_set = set(assign_u)
        for x in range(n):
            if x == u or x == v:
                continue
            if x in assign_u_set:
                edges.append(EdgeNum(parent_edge[u * n + x]))
            else:
                edges.append(EdgeNum(parent_edge[v * n + x]))
        edges.append(EdgeNum(ei))

    assert len(edges) == n - 1
    return MinimumDiameterSpanningTreeResult(edges=edges, diameter=Weight(min(best_vertex_diam, best_edge_diam)))
