"""Graph walks: DFS forests, cycle detection, Eulerian trails, and shortest walks."""

from __future__ import annotations

from collections.abc import Sequence

from collections import deque
from heapq import heappop, heappush
from typing import NamedTuple

from cplib.datastructure.queue import PersistentLeftistHeap
from cplib.graph.base import EdgeNum, Node, Weight
from cplib.graph.core import Graph


class DepthFirstSearchResult(NamedTuple):
    """
    Discovery and finish metadata of a depth-first search forest.

    Attributes:
        discovery: ``discovery[v]`` is the 1-based time when ``v`` is first visited.
        finish: ``finish[v]`` is the 1-based time when DFS leaves ``v``.
        parent: DFS forest parent of each vertex, or ``-1`` for roots.
        order: Vertices in discovery order.

    Space Complexity:
        O(n)
    """

    discovery: list[int]
    finish: list[int]
    parent: list[Node]
    order: list[Node]


def depth_first_search(graph: Graph, starts: Sequence[Node] | None = None) -> DepthFirstSearchResult:
    """
    Run DFS and return discovery and finish times.

    Args:
        graph: Input graph.
        starts: Root candidates for the DFS forest. If omitted, vertices are
            considered in ascending order.

    Returns:
        DFS metadata. Times are 1-based and advance on discovery and finish.

    Time Complexity:
        O(n + m)

    Space Complexity:
        O(n)
    """
    if starts is None:
        starts = [Node(i) for i in range(graph.n)]
    discovery = [0] * graph.n
    finish = [0] * graph.n
    parent = [Node(-1)] * graph.n
    order: list[Node] = []
    time = 0
    for start in starts:
        if discovery[start]:
            continue
        time += 1
        discovery[start] = time
        order.append(start)
        stack: list[tuple[Node, int]] = [(start, 0)]
        while stack:
            v, idx = stack[-1]
            if idx == len(graph.graph[v]):
                time += 1
                finish[v] = time
                stack.pop()
                continue
            u, _ = graph.graph[v][idx]
            stack[-1] = (v, idx + 1)
            if discovery[u]:
                continue
            parent[u] = v
            time += 1
            discovery[u] = time
            order.append(u)
            stack.append((u, 0))
    return DepthFirstSearchResult(discovery=discovery, finish=finish, parent=parent, order=order)

class CycleDetectionResult(NamedTuple):
    """
    Result of cycle detection.

    Attributes:
        found: Whether a cycle was found.
        length: Number of vertices in the returned cycle.
        nodes: Vertices on one detected cycle in traversal order.
        edges: Edge indices on that cycle in matching order.

    When ``found`` is ``False``, the remaining fields describe the empty cycle.
    For directed graphs, the reported order follows the traversal direction.
    For undirected graphs, the cycle is reported in one arbitrary orientation.

    Space Complexity:
        - ``O(k)``, where ``k`` is the reported cycle length.
    """

    found: bool
    length: int
    nodes: list[Node]
    edges: list[EdgeNum]


def cycle_detection(graph: Graph) -> CycleDetectionResult:
    """
    Detect one cycle in a graph.

    Args:
        graph: Input graph.

    Returns:
        CycleDetectionResult: Whether a cycle exists and one realizing cycle.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n)``
    """

    n = graph.n
    state = [0] * n
    pos = [-1] * n
    stack_v: list[Node] = []
    stack_e: list[EdgeNum] = []
    stack_it: list[int] = []

    for s in range(n):
        if state[s]:
            continue
        stack_v.append(Node(s))
        stack_it.append(0)
        stack_e.append(EdgeNum(-1))
        pos[s] = 0
        state[s] = 1

        while stack_v:
            v = stack_v[-1]
            it = stack_it[-1]
            if it == len(graph.graph[v]):
                pos[v] = -1
                stack_v.pop()
                stack_it.pop()
                stack_e.pop()
                state[v] = 2
                continue

            u, e = graph.graph[v][it]
            stack_it[-1] += 1
            if state[u] == 0:
                state[u] = 1
                stack_v.append(u)
                stack_it.append(0)
                stack_e.append(e)
                pos[u] = len(stack_v) - 1
            elif pos[u] != -1 and e != stack_e[-1]:
                start = pos[u]
                cycle_nodes = stack_v[start:]
                cycle_edges = stack_e[start + 1:] + [e]
                return CycleDetectionResult(
                    True,
                    len(cycle_nodes),
                    cycle_nodes,
                    cycle_edges,
                )

    return CycleDetectionResult(False, 0, [], [])


class EulerianTrailResult(NamedTuple):
    """
    Result of an Eulerian trail query.

    Attributes:
        exists: Whether an Eulerian trail exists.
        path_v: Vertices on one Eulerian trail.
        path_e: Edge indices on the same trail.

    When ``exists`` is ``False``, both path lists are empty.
    When it exists, ``path_e[i]`` connects ``path_v[i]`` to ``path_v[i + 1]``.
    The trail may be a circuit when the start and end vertices coincide.

    Space Complexity:
        - ``O(n + m)`` for the reported trail.
    """

    exists: bool
    path_v: list[Node]
    path_e: list[EdgeNum]


def eulerian_trail(graph: Graph) -> EulerianTrailResult:
    """
    Find one Eulerian trail using Hierholzer's algorithm.

    Args:
        graph: Input graph.

    Returns:
        EulerianTrailResult: Existence flag and one realizing trail if it exists.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n + m)``
    """

    n = graph.n
    m = graph.m
    if m == 0:
        return EulerianTrailResult(True, ([Node(0)] if n else []), [])

    if graph.is_directed:
        outdeg = [len(adj) for adj in graph.graph]
        diff = [outdeg[v] - graph.deg[v] for v in range(n)]
        plus = [Node(v) for v, d in enumerate(diff) if d == 1]
        minus = [Node(v) for v, d in enumerate(diff) if d == -1]
        zero = [v for v, d in enumerate(diff) if d == 0]
        if not (
            (len(plus) == len(minus) == 0)
            or (len(plus) == len(minus) == 1)
        ) or n - len(plus) - len(minus) != len(zero):
            return EulerianTrailResult(False, [], [])
        start = plus[0] if plus else Node(next(v for v, d in enumerate(outdeg) if d))
    else:
        deg = [len(adj) for adj in graph.graph]
        odd = [Node(v) for v, d in enumerate(deg) if d & 1]
        if not (len(odd) == 0 or len(odd) == 2):
            return EulerianTrailResult(False, [], [])
        start = odd[0] if odd else Node(next(v for v, d in enumerate(deg) if d))

    und_adj: list[list[Node]] = [[] for _ in range(n)]
    for u, v in graph.edges:
        und_adj[u].append(v)
        und_adj[v].append(u)

    active = [Node(v) for v in range(n) if und_adj[v]]
    seen = [False] * n
    que = deque([start])
    seen[start] = True
    while que:
        v = que.popleft()
        for w in und_adj[v]:
            if not seen[w]:
                seen[w] = True
                que.append(w)

    if any(not seen[v] for v in active):
        return EulerianTrailResult(False, [], [])

    adj = [list(reversed(list(graph.graph[v]))) for v in range(n)]
    used_edge = [False] * m
    stack_v: list[Node] = [start]
    stack_e: list[EdgeNum] = []
    path_v: list[Node] = []
    path_e: list[EdgeNum] = []

    while stack_v:
        v = stack_v[-1]
        while adj[v] and (not graph.is_directed and used_edge[adj[v][-1][1]]):
            adj[v].pop()

        if adj[v]:
            to, e = adj[v].pop()
            if not graph.is_directed and used_edge[e]:
                continue
            used_edge[e] = True
            stack_v.append(to)
            stack_e.append(e)
        else:
            path_v.append(stack_v.pop())
            if stack_e:
                path_e.append(stack_e.pop())

    if len(path_e) != m:
        return EulerianTrailResult(False, [], [])

    path_v.reverse()
    path_e.reverse()
    return EulerianTrailResult(True, path_v, path_e)


def k_shortest_walk(graph: Graph, source: Node, target: Node, k: int) -> list[Weight]:
    """
    Return the first ``k`` shortest walk lengths from ``source`` to ``target``.

    The graph must be directed with non-negative edge weights. Walks may repeat
    vertices and edges. The returned list is sorted in nondecreasing order and
    may contain fewer than ``k`` entries if fewer walks exist.

    This implementation follows Eppstein's sidetrack decomposition.

    Args:
        graph: Directed graph with non-negative edge weights.
        source: Start vertex.
        target: Goal vertex.
        k: Number of walk lengths to enumerate.

    Returns:
        list[Weight]: The first ``k`` walk lengths in sorted order.

    Raises:
        ValueError: If the graph contains a negative edge.

    Time Complexity:
        - ``O((n + m) log n + k log k)``

    Space Complexity:
        - ``O(n + m)``
    """

    if k <= 0:
        return []
    if graph.has_negative_edge:
        raise ValueError('k_shortest_walk requires non-negative edge weights')

    n = graph.n
    rev: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for edge_id, (u, v) in enumerate(graph.edges):
        rev[v].append((u, edge_id))

    dist = [Graph.dst_inf] * n
    next_v = [-1] * n
    next_e = [-1] * n
    dist[target] = Weight(0)
    pq: list[tuple[int, int]] = [(0, int(target))]
    while pq:
        d, v = heappop(pq)
        if d != dist[v]:
            continue
        for u, edge_id in rev[v]:
            nd = d + graph.wt[edge_id]
            if nd < dist[u]:
                dist[u] = Weight(nd)
                next_v[u] = v
                next_e[u] = edge_id
                heappush(pq, (nd, u))

    if dist[source] == Graph.dst_inf:
        return []

    children: list[list[int]] = [[] for _ in range(n)]
    for v in range(n):
        if next_v[v] != -1:
            children[next_v[v]].append(v)

    sidetrack_heap = PersistentLeftistHeap[tuple[int, int]]()

    local_root = [-1] * n
    for u in range(n):
        if dist[u] == Graph.dst_inf:
            continue
        root = -1
        tree_edge = next_e[u]
        for v, edge_id in graph.graph[u]:
            if dist[v] == Graph.dst_inf:
                continue
            if edge_id == tree_edge:
                continue
            delta = graph.wt[edge_id] + dist[v] - dist[u]
            root = sidetrack_heap.push(root, (int(delta), int(v)))
        local_root[u] = root

    root_heap = [-1] * n
    root_heap[target] = local_root[target]
    stack = [int(target)]
    while stack:
        v = stack.pop()
        for child in children[v]:
            root_heap[child] = sidetrack_heap.meld(local_root[child], root_heap[v])
            stack.append(child)

    answers = [dist[source]]
    cand: list[tuple[int, int]] = []

    def push_candidate(total: int, node: int) -> None:
        if node != -1:
            heappush(cand, (total, node))

    if root_heap[source] != -1:
        push_candidate(int(dist[source]) + sidetrack_heap.top(root_heap[source])[0], root_heap[source])
    while cand and len(answers) < k:
        total, node = heappop(cand)
        answers.append(Weight(total))
        (delta, to), popped = sidetrack_heap.pop(node)
        if not sidetrack_heap.is_empty(popped):
            push_candidate(total - delta + sidetrack_heap.top(popped)[0], popped)
        child_root = root_heap[to]
        if child_root != -1:
            push_candidate(total + sidetrack_heap.top(child_root)[0], child_root)
    return answers
