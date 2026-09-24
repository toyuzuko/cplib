"""Reachability, strongly connected components, DAG order, and dominators."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from typing import NamedTuple

from cplib.datastructure.dsu import QueryDSU
from cplib.graph.base import Node
from cplib.graph.core import CSRGraph, Graph


class NodeGroupingResult(NamedTuple):
    """
    Partition of vertices into groups.

    Attributes:
        n: Number of groups.
        group: ``group[v]`` is the group id assigned to vertex ``v``.

    The numbering of groups depends on the algorithm that produced the result.
    Group ids are dense in the range ``[0, n)``.
    The result object is shared by several decomposition utilities.

    Space Complexity:
        - ``O(n)``
    """

    n: int
    group: list[int]


def strongly_connected_components(graph: Graph) -> NodeGroupingResult:
    """
    Compute strongly connected components of a directed graph.

    Args:
        graph: Directed graph.

    Returns:
        NodeGroupingResult: SCC count and component id of each vertex.

    Raises:
        ValueError: If ``graph`` is undirected.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n + m)``
    """

    if not graph.is_directed:
        raise ValueError('The graph must be directed')
    n = graph.n
    vis = [False] * n
    done = [False] * n
    order: list[Node] = []
    for s in range(n):
        if vis[s]:
            continue
        stack = [~s, s]
        while stack:
            v = stack.pop()
            if v >= 0:
                if vis[v]:
                    continue
                vis[v] = True
                for u, _ in graph.graph[v]:
                    if not vis[u]:
                        stack.append(~u)
                        stack.append(u)
            else:
                v = ~v
                if done[v]:
                    continue
                done[v] = True
                order.append(Node(v))
    rev: list[list[Node]] = [[] for _ in range(n)]
    for v in range(n):
        for u, _ in graph.graph[v]:
            rev[u].append(Node(v))
    order.reverse()
    scc = [-1] * n
    cnt = 0
    for s in order:
        if scc[s] != -1:
            continue
        stack = [s]
        scc[s] = cnt
        while stack:
            v = stack.pop()
            for u in rev[v]:
                if scc[u] == -1:
                    scc[u] = cnt
                    stack.append(u)
        cnt += 1
    return NodeGroupingResult(n=cnt, group=scc)


def _strongly_connected_components_csr(n: int, start: Sequence[int], to: Sequence[int]) -> NodeGroupingResult:
    vis = [False] * n
    order: list[int] = []
    for s in range(n):
        if vis[s]:
            continue
        vis[s] = True
        stack = [s]
        index = [start[s]]
        while stack:
            v = stack[-1]
            i = index[-1]
            end = start[v + 1]
            while i < end and vis[to[i]]:
                i += 1
            if i == end:
                order.append(v)
                stack.pop()
                index.pop()
            else:
                u = int(to[i])
                index[-1] = i + 1
                vis[u] = True
                stack.append(u)
                index.append(start[u])

    m = len(to)
    reverse_degree = [0] * n
    for u in to:
        reverse_degree[u] += 1
    reverse_start = [0] * (n + 1)
    for i in range(n):
        reverse_start[i + 1] = reverse_start[i] + reverse_degree[i]
    reverse_to = [0] * m
    cursor = reverse_start[:]
    for v in range(n):
        for i in range(start[v], start[v + 1]):
            u = int(to[i])
            p = cursor[u]
            reverse_to[p] = v
            cursor[u] += 1

    scc = [-1] * n
    cnt = 0
    for s in reversed(order):
        if scc[s] != -1:
            continue
        stack = [s]
        scc[s] = cnt
        while stack:
            v = stack.pop()
            for i in range(reverse_start[v], reverse_start[v + 1]):
                u = reverse_to[i]
                if scc[u] == -1:
                    scc[u] = cnt
                    stack.append(u)
        cnt += 1
    return NodeGroupingResult(n=cnt, group=scc)


def strongly_connected_components_raw_csr(n: int, start: Sequence[int], to: Sequence[int]) -> NodeGroupingResult:
    """
    Compute strongly connected components from raw CSR arrays.

    Args:
        n: Number of vertices.
        start: CSR offsets of length ``n + 1``.
        to: CSR destination array.

    Returns:
        NodeGroupingResult: SCC count and component id of each vertex.

    Time Complexity:
        O(n + m), where ``m = len(to)``.

    Space Complexity:
        O(n + m)
    """
    return _strongly_connected_components_csr(n, start, to)


def strongly_connected_components_csr(graph: CSRGraph) -> NodeGroupingResult:
    """
    Compute strongly connected components of a directed CSR graph.

    Args:
        graph: Directed CSR graph.

    Returns:
        NodeGroupingResult: SCC count and component id of each vertex.

    Raises:
        ValueError: If ``graph`` is undirected.

    Time Complexity:
        O(n + m)

    Space Complexity:
        O(n + m)
    """
    if not graph.is_directed:
        raise ValueError('The graph must be directed')
    return _strongly_connected_components_csr(graph.n, graph.start, graph.to)


def topological_sort(graph: Graph) -> list[Node]:
    """
    Return one topological order of a directed acyclic graph.

    Args:
        graph: Directed graph.

    Returns:
        list[Node]: Vertices in topological order.

    Raises:
        ValueError: If ``graph`` is undirected or contains a cycle.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n)``
    """

    if not graph.is_directed:
        raise ValueError('The graph must be directed')
    state = [0] * graph.n
    order: list[Node] = []
    for s in range(graph.n):
        if state[s]:
            continue
        state[s] = 1
        stack = [(Node(s), 0)]
        while stack:
            v, i = stack[-1]
            if i == len(graph.graph[v]):
                state[v] = 2
                order.append(v)
                stack.pop()
                continue
            u, _ = graph.graph[v][i]
            stack[-1] = (v, i + 1)
            if state[u] == 0:
                state[u] = 1
                stack.append((u, 0))
            elif state[u] == 1:
                raise ValueError('The graph must be acyclic')
    order.reverse()
    return order


class OfflineDagReachability:
    """
    Offline reachability queries on a DAG.

    The query set must be known before solving. Queries are answered by batching
    target vertices into bitsets and propagating them in reverse topological
    order.

    Space Complexity:
        O(nB / w), where ``B`` is ``block_size`` and ``w`` is the machine word
        size used by Python integers.
    """

    def __init__(self, graph: Graph, topological_order: Sequence[Node] | None = None, block_size: int = 4096) -> None:
        """
        Initialize the offline DAG reachability solver.

        Args:
            graph: Directed acyclic graph.
            topological_order: Optional topological order. If omitted, it is
                computed from ``graph``.
            block_size: Number of queries packed into one bitset batch.

        Returns:
            None.

        Raises:
            ValueError: If ``graph`` is undirected, cyclic, or ``block_size`` is
                not positive.

        Time Complexity:
            O(n + m)
        """
        if not graph.is_directed:
            raise ValueError('The graph must be directed')
        if block_size <= 0:
            raise ValueError('block_size must be positive')
        self.graph = graph
        self.block_size = block_size
        if topological_order is None:
            self.order = [int(v) for v in topological_sort(graph)]
        else:
            self.order = [int(v) for v in topological_order]
            if len(self.order) != graph.n or sorted(self.order) != list(range(graph.n)):
                raise ValueError('topological_order must be a permutation of vertices')
            position = [0] * graph.n
            for i, v in enumerate(self.order):
                position[v] = i
            for v in range(graph.n):
                for to, _ in graph.graph[v]:
                    if position[v] >= position[int(to)]:
                        raise ValueError('topological_order must be a topological order')

    def solve(self, queries: Sequence[tuple[Node, Node]]) -> list[bool]:
        """
        Answer reachability queries.

        Args:
            queries: Pairs ``(source, target)``. A vertex is reachable from
                itself.

        Returns:
            Boolean answers in the same order as ``queries``.

        Raises:
            ValueError: If a query vertex is outside ``[0, n)``.

        Time Complexity:
            O(ceil(q / B) * (n + m) * B / w + q), where ``B`` is
            ``block_size``.

        Space Complexity:
            O(nB / w + q)
        """
        normalized: list[tuple[int, int]] = []
        for source, target in queries:
            s = int(source)
            t = int(target)
            if not 0 <= s < self.graph.n or not 0 <= t < self.graph.n:
                raise ValueError('query vertices must be within [0, n)')
            normalized.append((s, t))

        answers = [False] * len(normalized)
        for left in range(0, len(normalized), self.block_size):
            right = min(left + self.block_size, len(normalized))
            reach = [0] * self.graph.n
            for i in range(left, right):
                _, target = normalized[i]
                reach[target] |= 1 << (i - left)
            for vertex in reversed(self.order):
                mask = reach[vertex]
                for to, _ in self.graph.graph[vertex]:
                    mask |= reach[int(to)]
                reach[vertex] = mask
            for i in range(left, right):
                source, _ = normalized[i]
                answers[i] = bool((reach[source] >> (i - left)) & 1)
        return answers


def offline_reachability(graph: Graph, queries: Sequence[tuple[Node, Node]], block_size: int = 4096) -> list[bool]:
    """
    Offline reachability queries on a directed graph.

    The graph is first compressed into strongly connected components. The
    resulting condensation DAG is then solved by ``OfflineDagReachability``.

    Args:
        graph: Directed graph.
        queries: Pairs ``(source, target)``.
        block_size: Number of queries packed into one bitset batch.

    Returns:
        Boolean answers in the same order as ``queries``.

    Raises:
        ValueError: If ``graph`` is undirected or query vertices are invalid.

    Time Complexity:
        O(n + m + ceil(q / B) * (c + e) * B / w + q), where ``c`` and ``e`` are
        the number of vertices and edges of the condensation DAG.

    Space Complexity:
        O(n + m + cB / w + q)
    """
    if not graph.is_directed:
        raise ValueError('The graph must be directed')
    components = strongly_connected_components(graph)
    component_graph = Graph(components.n, is_directed=True)
    seen_edges: set[int] = set()
    for vertex in range(graph.n):
        source = components.group[vertex]
        for to, _ in graph.graph[vertex]:
            target = components.group[int(to)]
            if source == target:
                continue
            key = source * components.n + target
            if key in seen_edges:
                continue
            seen_edges.add(key)
            component_graph.add_edge(Node(source), Node(target))

    component_queries: list[tuple[Node, Node]] = []
    deferred_indices: list[int] = []
    answers = [False] * len(queries)
    for i, (source, target) in enumerate(queries):
        s = int(source)
        t = int(target)
        if not 0 <= s < graph.n or not 0 <= t < graph.n:
            raise ValueError('query vertices must be within [0, n)')
        source_component = components.group[s]
        target_component = components.group[t]
        if source_component == target_component:
            answers[i] = True
        else:
            deferred_indices.append(i)
            component_queries.append((Node(source_component), Node(target_component)))

    if component_queries:
        component_answers = OfflineDagReachability(component_graph, block_size=block_size).solve(component_queries)
        for i, answer in zip(deferred_indices, component_answers):
            answers[i] = answer
    return answers


def dominator_tree(graph: Graph, root: Node) -> list[Node]:
    """
    Compute immediate dominators from one root.

    This implements the Lengauer-Tarjan algorithm on the directed graph
    reachable from ``root``.

    Args:
        graph: Directed graph.
        root: Start vertex of the flow graph.

    Returns:
        list[Node]: Array ``idom`` where ``idom[v]`` is the immediate dominator
        of ``v``. Unreachable vertices receive ``-1`` and ``idom[root] = root``.

    Time Complexity:
        - Near-linear, typically ``O((n + m) alpha(n))``

    Space Complexity:
        - ``O(n + m)``
    """

    stack = [root]
    visited = [False] * graph.n
    par = [-1] * graph.n
    idx = [-1] * graph.n
    order: list[int] = []

    while stack:
        v = stack.pop()
        if visited[v]:
            continue
        visited[v] = True
        order.append(v)
        idx[v] = len(order) - 1
        for adj, _ in graph.graph[v]:
            if not visited[adj]:
                par[adj] = v
                stack.append(adj)

    rev: list[list[int]] = [[] for _ in range(graph.n)]
    for v in range(graph.n):
        for a, _ in graph.graph[v]:
            rev[a].append(v)

    bucket: list[list[int]] = [[] for _ in range(graph.n)]
    idom = [Node(-1)] * graph.n
    sdom = [Node(i) for i in range(graph.n)]
    evals = [-1] * graph.n
    dsu = QueryDSU(graph.n, lambda x: idx[sdom[x]], min)

    for w in order[1:][::-1]:
        for v in rev[w]:
            if idx[v] == -1:
                continue
            u = dsu.eval(v)
            if idx[sdom[u]] < idx[sdom[w]]:
                sdom[w] = sdom[u]
        bucket[sdom[w]].append(w)
        for v in bucket[par[w]]:
            evals[v] = dsu.eval(v)
        bucket[par[w]].clear()
        dsu.link(w, par[w])

    for w in order[1:]:
        v = evals[w]
        if sdom[w] == sdom[v]:
            idom[w] = sdom[w]
        else:
            idom[w] = idom[v]

    for v in range(graph.n):
        if par[v] == -1:
            idom[v] = Node(v) if v == root else Node(-1)

    return idom


def complement_connected_components(graph: Graph) -> NodeGroupingResult:
    """
    Compute connected components of the complement of an undirected graph.

    Args:
        graph: Undirected graph.

    Returns:
        NodeGroupingResult: Component count and component id of each vertex in
        the complement graph.

    Raises:
        ValueError: If ``graph`` is directed.

    Time Complexity:
        O(n^2) in the size of the processed input or stored data

    Space Complexity:
        O(n + m) in the size of newly allocated output or auxiliary storage
    """

    if graph.is_directed:
        raise ValueError('The graph must be undirected')
    n = graph.n
    unvis = set(range(n))
    group = [-1] * n
    adj: list[set[int]] = [set() for _ in range(n)]
    for u, v in graph.edges:
        adj[u].add(v)
        adj[v].add(u)
    k = 0
    for s in range(n):
        if s not in unvis:
            continue
        que = deque([s])
        unvis.discard(s)
        while que:
            v = que.popleft()
            group[v] = k
            to_vis: list[int] = []
            for u in unvis:
                if u not in adj[v]:
                    to_vis.append(u)
            for u in to_vis:
                que.append(u)
                unvis.discard(u)
        k += 1
    return NodeGroupingResult(n=k, group=group)
