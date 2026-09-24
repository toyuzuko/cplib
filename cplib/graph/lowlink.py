"""Lowlink analysis, biconnected components, and block-cut and bridge forests."""

from __future__ import annotations

from typing import NamedTuple

from cplib.graph.base import EdgeNum, Node
from cplib.graph.core import Graph

__all__ = ['LowLinkResult', 'LowLinkAnalysisResult', 'analyze_lowlink', 'lowlink', 'BlockCutTreeResult', 'BridgeTreeResult', 'biconnected_components', 'block_cut_tree', 'two_edge_connected_components', 'bridge_tree']


class LowLinkResult(NamedTuple):
    """
    Result of lowlink analysis on an undirected graph.

    Attributes:
        order: DFS discovery order for each vertex.
        low: Lowlink value for each vertex.
        articulation_points: Articulation points in ascending vertex order.
        bridges: Bridge edge indices in ascending edge-index order.

    This is the public summary returned by :func:`lowlink`.
    More detailed component data is available from :func:`analyze_lowlink`.
    The arrays are indexed by original vertex id.

    Space Complexity:
        - ``O(n + b)``, where ``b`` is the number of bridges.
    """

    order: list[int]
    low: list[int]
    articulation_points: list[Node]
    bridges: list[EdgeNum]


class LowLinkAnalysisResult(NamedTuple):
    """Lowlink analysis including vertex-biconnected components.

    Attributes:
        order: DFS discovery order of each vertex.
        low: Lowest discovery order reachable by a DFS subtree and a back edge.
        articulation: Whether each vertex is an articulation point.
        bridges: Original edge indices of bridges, in ascending order.
        biconnected_components: Vertex lists for vertex-biconnected components.
            Articulation vertices can belong to multiple components. Isolated
            vertices form singleton components. Component and vertex order
            follows traversal and is not guaranteed to be sorted.

    Space Complexity:
        O(n + m) for n vertices and m edges.
    """
    order: list[int]
    low: list[int]
    articulation: list[bool]
    bridges: list[EdgeNum]
    biconnected_components: list[list[Node]]


def _append_component(
    graph: Graph,
    edge_stack: list[int],
    seen: list[int],
    components: list[list[Node]],
    stop_edge: int | None,
) -> None:
    if not edge_stack:
        return
    component_id = len(components)
    component: list[Node] = []
    while edge_stack:
        edge_index = edge_stack.pop()
        u, v = graph.edges[edge_index]
        if seen[u] != component_id:
            seen[u] = component_id
            component.append(Node(u))
        if seen[v] != component_id:
            seen[v] = component_id
            component.append(Node(v))
        if stop_edge is not None and edge_index == stop_edge:
            break
    if component:
        components.append(component)


def analyze_lowlink(graph: Graph) -> LowLinkAnalysisResult:
    """
    Run lowlink analysis, including vertex-biconnected components.

    Args:
        graph: Undirected graph to analyze.

    Returns:
        LowLinkAnalysisResult: DFS order, lowlink values, articulation flags, bridges,
        and biconnected components.

    Raises:
        ValueError: If the graph is directed.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n + m)``
    """
    if graph.is_directed:
        raise ValueError('graph must be undirected')
    n = graph.n
    order = [-1] * n
    low = [0] * n
    parent = [-1] * n
    parent_edge = [-1] * n
    child_count = [0] * n
    articulation = [False] * n
    bridges: list[EdgeNum] = []
    edge_stack: list[int] = []
    seen = [-1] * n
    components: list[list[Node]] = []

    timer = 0
    for root in range(n):
        if order[root] != -1:
            continue
        component_stack_size = len(edge_stack)
        stack: list[tuple[int, int, int, int]] = [(root, -1, -1, 0)]
        while stack:
            v, p, pe, index = stack.pop()
            if index == 0 and order[v] == -1:
                order[v] = timer
                low[v] = timer
                timer += 1

            if index < len(graph.graph[v]):
                to, edge_index = graph.graph[v][index]
                stack.append((v, p, pe, index + 1))
                if edge_index == pe:
                    continue
                if order[to] == -1:
                    parent[to] = v
                    parent_edge[to] = edge_index
                    child_count[v] += 1
                    edge_stack.append(edge_index)
                    stack.append((to, v, edge_index, 0))
                elif order[to] < order[v]:
                    low[v] = min(low[v], order[to])
                    edge_stack.append(edge_index)
                continue

            if p == -1:
                if child_count[v] > 1:
                    articulation[v] = True
                if child_count[v] == 0:
                    components.append([Node(v)])
                if len(edge_stack) > component_stack_size:
                    _append_component(graph, edge_stack, seen, components, stop_edge=None)
                continue

            low[p] = min(low[p], low[v])
            if low[v] > order[p]:
                bridges.append(EdgeNum(parent_edge[v]))
            if low[v] >= order[p]:
                if parent[p] != -1 or child_count[p] > 1:
                    articulation[p] = True
                _append_component(graph, edge_stack, seen, components, stop_edge=parent_edge[v])

    bridges.sort()
    return LowLinkAnalysisResult(
        order=order,
        low=low,
        articulation=articulation,
        bridges=bridges,
        biconnected_components=components,
    )


def lowlink(graph: Graph) -> LowLinkResult:
    """
    Compute lowlink information for an undirected graph.

    Args:
        graph: Undirected graph to analyze.

    Returns:
        ``LowLinkResult`` containing DFS order, lowlink values, articulation
        points, and bridge edge indices.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n + m)``
    """

    analysis = analyze_lowlink(graph)
    articulation_points = [
        Node(v) for v, is_art in enumerate(analysis.articulation) if is_art
    ]
    return LowLinkResult(
        order=analysis.order,
        low=analysis.low,
        articulation_points=articulation_points,
        bridges=analysis.bridges,
    )


class BlockCutTreeResult(NamedTuple):
    """
    Result of block-cut forest construction.

    Attributes:
        graph: Adjacency list of the block-cut forest.
        components: Biconnected components, indexed by component node id.
        articulation_points: Original articulation vertices.
        component_node: Identity map for component-node ids.
        articulation_node: ``articulation_node[v]`` is the forest node
            representing articulation vertex ``v``, or ``-1`` if ``v`` is not
            an articulation point.
        vertex_node: Forest node corresponding to original vertex ``v``. This
            is the articulation node for articulation points and the unique
            component node otherwise.

    Space Complexity:
        O(n + m), including component memberships and vertex mappings.
    """

    graph: list[list[int]]
    components: list[list[Node]]
    articulation_points: list[Node]
    component_node: list[int]
    articulation_node: list[int]
    vertex_node: list[int]


class BridgeTreeResult(NamedTuple):
    """
    Result of bridge-forest construction.

    Attributes:
        graph: Adjacency list of the bridge forest.
        components: Two-edge-connected components.
        component_id: ``component_id[v]`` is the component containing ``v``.
        bridges: Edge indices of the original bridge edges.

    Each forest node corresponds to one two-edge-connected component, and each
    bridge becomes one forest edge between the two incident components.

    The forest may contain multiple connected components when the input graph
    is disconnected.

    Space Complexity:
        O(n), including component memberships and the bridge forest.
    """

    graph: list[list[int]]
    components: list[list[Node]]
    component_id: list[int]
    bridges: list[EdgeNum]


def biconnected_components(graph: Graph) -> list[list[Node]]:
    """
    Enumerate biconnected components as vertex sets.

    Each component is returned as a list of original vertex indices. Isolated
    vertices appear as singleton components.

    Args:
        graph: Undirected graph to decompose.

    Returns:
        List of biconnected components.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n + m)``

    Examples:
        >>> g = Graph(3)
        >>> g.add_edge(0, 1)
        >>> g.add_edge(1, 2)
        >>> biconnected_components(g)
        [[1, 2], [0, 1]]
    """

    return analyze_lowlink(graph).biconnected_components


def block_cut_tree(graph: Graph) -> BlockCutTreeResult:
    """
    Build the block-cut forest of an undirected graph.

    Component nodes occupy indices ``[0, bcc_count)``. Articulation nodes are
    appended after them. The result is a forest, so isolated vertices and
    disconnected graphs are handled naturally.

    Args:
        graph: Undirected graph to compress.

    Returns:
        ``BlockCutTreeResult`` with compressed adjacency and mapping arrays.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n + m)``

    Examples:
        >>> g = Graph(3)
        >>> g.add_edge(0, 1)
        >>> g.add_edge(1, 2)
        >>> result = block_cut_tree(g)
        >>> len(result.components)
        2
    """

    analysis = analyze_lowlink(graph)
    components = analysis.biconnected_components
    articulation_points = [Node(v) for v, is_art in enumerate(analysis.articulation) if is_art]
    articulation_node = [-1] * graph.n
    component_count = len(components)
    for offset, vertex in enumerate(articulation_points):
        articulation_node[vertex] = component_count + offset

    forest: list[list[int]] = [[] for _ in range(component_count + len(articulation_points))]
    component_node = list(range(component_count))
    vertex_node = [-1] * graph.n

    for component_index, component in enumerate(components):
        for vertex in component:
            articulation_index = articulation_node[vertex]
            if articulation_index == -1:
                vertex_node[vertex] = component_index
                continue
            forest[component_index].append(articulation_index)
            forest[articulation_index].append(component_index)
            vertex_node[vertex] = articulation_index

    return BlockCutTreeResult(
        graph=forest,
        components=components,
        articulation_points=articulation_points,
        component_node=component_node,
        articulation_node=articulation_node,
        vertex_node=vertex_node,
    )


def two_edge_connected_components(graph: Graph) -> list[list[Node]]:
    """
    Enumerate two-edge-connected components.

    Vertices belong to the same component iff no bridge separates them.

    Args:
        graph: Undirected graph to decompose.

    Returns:
        List of two-edge-connected components.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n + m)``

    Examples:
        >>> g = Graph(4)
        >>> g.add_edge(0, 1)
        >>> g.add_edge(1, 2)
        >>> g.add_edge(2, 0)
        >>> g.add_edge(2, 3)
        >>> two_edge_connected_components(g)
        [[0, 2, 1], [3]]
    """

    analysis = analyze_lowlink(graph)
    bridge_set = set(analysis.bridges)
    component_id = [-1] * graph.n
    components: list[list[Node]] = []

    for start in range(graph.n):
        if component_id[start] != -1:
            continue
        cid = len(components)
        component_id[start] = cid
        stack = [start]
        component: list[Node] = []
        while stack:
            v = stack.pop()
            component.append(Node(v))
            for to, edge_index in graph.graph[v]:
                if edge_index in bridge_set or component_id[to] != -1:
                    continue
                component_id[to] = cid
                stack.append(to)
        components.append(component)

    return components


def bridge_tree(graph: Graph) -> BridgeTreeResult:
    """
    Build the bridge forest of an undirected graph.

    Each node of the returned forest represents one two-edge-connected
    component. Bridge edges become forest edges between the compressed nodes.

    Args:
        graph: Undirected graph to compress.

    Returns:
        ``BridgeTreeResult`` with component mapping and compressed adjacency.

    Time Complexity:
        - ``O(n + m)``

    Space Complexity:
        - ``O(n + m)``

    Examples:
        >>> g = Graph(3)
        >>> g.add_edge(0, 1)
        >>> g.add_edge(1, 2)
        >>> result = bridge_tree(g)
        >>> len(result.components)
        3
    """

    analysis = analyze_lowlink(graph)
    bridge_set = set(analysis.bridges)
    component_id = [-1] * graph.n
    components: list[list[Node]] = []

    for start in range(graph.n):
        if component_id[start] != -1:
            continue
        cid = len(components)
        component_id[start] = cid
        stack = [start]
        component: list[Node] = []
        while stack:
            v = stack.pop()
            component.append(Node(v))
            for to, edge_index in graph.graph[v]:
                if edge_index in bridge_set or component_id[to] != -1:
                    continue
                component_id[to] = cid
                stack.append(to)
        components.append(component)

    forest: list[list[int]] = [[] for _ in range(len(components))]
    for edge_index in analysis.bridges:
        u, v = graph.edges[edge_index]
        cu = component_id[u]
        cv = component_id[v]
        forest[cu].append(cv)
        forest[cv].append(cu)

    return BridgeTreeResult(
        graph=forest,
        components=components,
        component_id=component_id,
        bridges=analysis.bridges,
    )
