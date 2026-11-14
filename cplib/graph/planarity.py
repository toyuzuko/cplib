"""Planarity testing, combinatorial embeddings, faces, and planar duals."""

from __future__ import annotations

from typing import NamedTuple

from cplib.graph.base import Edge, Node, Weight
from cplib.graph.core import Graph

__all__ = ['PlanarEmbeddingResult', 'PlanarFacesResult', 'is_planar', 'planar_embedding', 'planar_faces', 'planar_dual']


class PlanarEmbeddingResult(NamedTuple):
    """Snapshot of a planar embedding with original edge IDs.

    Half-edge ``2 * e`` follows ``edges[e]`` from its first endpoint to its
    second; ``2 * e + 1`` follows the reverse direction. Reversal is ``h ^ 1``.
    A loop also has two distinct half-edges. No vertex coordinates are stored.

    Attributes:
        rotation: Outgoing half-edge IDs around each vertex in clockwise order.
            The starting position and the embedding itself are not canonical.
        edges: Copy of the original endpoint pairs, in original edge-ID order.
        weights: Copy of the original edge weights, in the same order.
        component: Connected-component ID of each vertex. IDs are consecutive
            from zero; isolated vertices also have their own component.

    Treat the stored lists as read-only when passing this result to the face
    and dual builders. Later changes to the input graph do not affect it.

    Space Complexity:
        O(n + m).
    """

    rotation: list[list[int]]
    edges: list[Edge]
    weights: list[Weight]
    component: list[int]


class PlanarFacesResult(NamedTuple):
    """Face boundaries and half-edge-to-face mapping of a planar embedding.

    Attributes:
        boundaries: For each face, a list of boundary walks. Each walk lists
            half-edge IDs with that face on their left. Vertices and edges
            may repeat along a walk, for example on both sides of a bridge.
        face_of_half_edge: Face ID on the left of each half-edge.

    Face zero is the chosen outer face. For disconnected graphs, one face
    from each component is chosen as exterior and these faces are merged;
    components are placed side by side, without nesting. The outer face can
    therefore have multiple boundary walks. Isolated vertices contribute no
    walk. Even an edgeless or empty graph has one outer face.

    Space Complexity:
        O(n + m).
    """

    boundaries: list[list[list[int]]]
    face_of_half_edge: list[int]


def is_planar(graph: Graph) -> bool:
    """Return whether an undirected graph admits a planar embedding.

    Use the Left-Right planarity test with iterative DFS and bucket sorting.
    The input graph is not modified. Self-loops and parallel edges are
    ignored, and edge weights have no effect on the result. Disconnected
    graphs, including the empty graph, are supported.

    Args:
        graph: Undirected graph to test.

    Returns:
        True if the graph can be drawn in the plane without edge crossings.

    Raises:
        ValueError: If the graph is directed.

    Time Complexity:
        O(n + m), where n and m are the input vertex and edge counts.

    Space Complexity:
        O(n + m).

    References:
        Ulrik Brandes, The Left-Right Planarity Test, 2009, Sections 6.1-6.2.
        https://www.uni-konstanz.de/algo/publications/b-lrpt-sub.pdf

    Examples:
        >>> g = Graph(4)
        >>> for u in range(4):
        ...     for v in range(u + 1, 4):
        ...         g.add_edge(Node(u), Node(v))
        >>> is_planar(g)
        True
        >>> g = Graph(6)
        >>> for u in range(3):
        ...     for v in range(3, 6):
        ...         g.add_edge(Node(u), Node(v))
        >>> is_planar(g)
        False
    """
    if graph.is_directed:
        raise ValueError('graph must be undirected')
    n = graph.n
    if n < 5:
        return True
    return _planar_rotation(graph, False) is not None


def planar_embedding(graph: Graph) -> PlanarEmbeddingResult | None:
    """Construct a planar embedding of an undirected graph, if one exists.

    Use the iterative Left-Right algorithm with bucket sorting. Preserve
    all original edge IDs, including parallel edges and self-loops. The
    result owns copies of the endpoints and weights; the input is unchanged.

    Args:
        graph: Undirected graph, possibly disconnected or empty.

    Returns:
        A clockwise rotation system, or None if the graph is not planar.

    Raises:
        ValueError: If the graph is directed.

    Time Complexity:
        O(n + m).

    Space Complexity:
        O(n + m).

    References:
        Ulrik Brandes, The Left-Right Planarity Test, 2009, Section 6.
        https://www.uni-konstanz.de/algo/publications/b-lrpt-sub.pdf

    Examples:
        >>> g = Graph(3)
        >>> for u, v in ((0, 1), (1, 2), (2, 0)):
        ...     g.add_edge(Node(u), Node(v))
        >>> embedding = planar_embedding(g)
        >>> embedding is not None
        True
        >>> sorted(h for row in embedding.rotation for h in row)
        [0, 1, 2, 3, 4, 5]
    """
    if graph.is_directed:
        raise ValueError('graph must be undirected')
    result = _planar_rotation(graph, True)
    if result is None:
        return None
    rotation, component = result
    return PlanarEmbeddingResult(rotation, graph.edges[:], graph.wt[:], component)


def planar_faces(embedding: PlanarEmbeddingResult) -> PlanarFacesResult:
    """Enumerate all faces, merging component exteriors into outer face zero.

    Args:
        embedding: Unmodified result of planar_embedding.

    Returns:
        Boundary walks and the face on the left of every half-edge. Face
        order and the choice of exterior in each component are arbitrary.

    Time Complexity:
        O(n + m).

    Space Complexity:
        O(n + m).

    Examples:
        >>> g = Graph(2)
        >>> g.add_edge(Node(0), Node(1))
        >>> embedding = planar_embedding(g)
        >>> faces = planar_faces(embedding)
        >>> faces.boundaries
        [[[0, 1]]]
        >>> faces.face_of_half_edge
        [0, 0]
    """
    m = len(embedding.edges)
    clockwise = [-1] * (2 * m)
    for row in embedding.rotation:
        for i, half_edge in enumerate(row):
            clockwise[half_edge] = row[(i + 1) % len(row)]
    boundaries: list[list[list[int]]] = [[]]
    face_of_half_edge = [-1] * (2 * m)
    exterior_seen = bytearray(len(embedding.rotation))
    for start in range(2 * m):
        if face_of_half_edge[start] != -1:
            continue
        v = embedding.edges[start // 2][start & 1]
        component = embedding.component[v]
        if exterior_seen[component]:
            face = len(boundaries)
            boundaries.append([])
        else:
            exterior_seen[component] = 1
            face = 0
        walk: list[int] = []
        half_edge = start
        while face_of_half_edge[half_edge] == -1:
            face_of_half_edge[half_edge] = face
            walk.append(half_edge)
            half_edge = clockwise[half_edge ^ 1]
        boundaries[face].append(walk)
    return PlanarFacesResult(boundaries, face_of_half_edge)


def planar_dual(embedding: PlanarEmbeddingResult) -> Graph:
    """Build the weighted planar dual, preserving original edge IDs.

    Args:
        embedding: Unmodified result of planar_embedding.

    Returns:
        Undirected graph whose vertices are face IDs from planar_faces.
        Dual edge e joins the faces of half-edges 2*e and 2*e+1, and has
        embedding.weights[e]. Bridges become loops; multiple edges are
        retained. The chosen common outer face has vertex ID zero.

    Time Complexity:
        O(n + m).

    Space Complexity:
        O(n + m).

    Examples:
        >>> g = Graph(2)
        >>> g.add_edge(Node(0), Node(1), Weight(7))
        >>> dual = planar_dual(planar_embedding(g))
        >>> (dual.n, dual.edges, dual.wt)
        (1, [(0, 0)], [7])
    """
    faces = planar_faces(embedding)
    dual = Graph(len(faces.boundaries))
    for edge, weight in enumerate(embedding.weights):
        dual.add_edge(Node(faces.face_of_half_edge[2 * edge]), Node(faces.face_of_half_edge[2 * edge + 1]), weight)
    return dual


def _planar_rotation(graph: Graph, build_embedding: bool) -> tuple[list[list[int]], list[int]] | None:
    n = graph.n

    # Vertex stamps remove parallel edges in deterministic linear time.
    adjacency: list[list[int]] = [[] for _ in range(n)]
    source: list[int] = []
    target: list[int] = []
    seen = [-1] * n
    group_index = [-1] * n
    groups: list[list[int]] = []
    for v in range(n):
        for w, original_edge in graph.graph[v]:
            if w <= v:
                continue
            if seen[w] == v:
                if build_embedding:
                    groups[group_index[w]].append(int(original_edge))
                continue
            seen[w] = v
            edge = len(source)
            if build_embedding:
                group_index[w] = edge
                groups.append([int(original_edge)])
            source.append(v)
            target.append(int(w))
            adjacency[v].append(edge)
            adjacency[w].append(edge)
    m = len(source)
    if n >= 3 and m > 3 * n - 6:
        return None

    # Orient tree edges toward descendants and back edges toward ancestors.
    height = [-1] * n
    parent = [-1] * n
    cursor = [0] * n
    oriented = bytearray(m)
    order: list[int] = []
    roots: list[int] = []
    component = [-1] * n
    low = [0] * m
    low2 = [0] * m
    nesting = [0] * m
    for root in range(n):
        if height[root] != -1:
            continue
        component[root] = len(roots)
        roots.append(root)
        height[root] = 0
        vertices = [root]
        while vertices:
            v = vertices[-1]
            if cursor[v] == len(adjacency[v]):
                vertices.pop()
                continue
            edge = adjacency[v][cursor[v]]
            cursor[v] += 1
            if oriented[edge]:
                continue
            oriented[edge] = 1
            w = target[edge] if source[edge] == v else source[edge]
            source[edge], target[edge] = v, w
            order.append(edge)
            low[edge] = low2[edge] = height[v]
            if height[w] == -1:
                parent[w] = edge
                component[w] = component[v]
                height[w] = height[v] + 1
                vertices.append(w)
            else:
                low[edge] = height[w]

    # Every descendant edge precedes its parent in reverse discovery order.
    for edge in reversed(order):
        v = source[edge]
        nesting[edge] = 2 * low[edge] + int(low2[edge] < height[v])
        incoming = parent[v]
        if incoming == -1:
            continue
        if low[edge] < low[incoming]:
            low2[incoming] = min(low[incoming], low2[edge])
            low[incoming] = low[edge]
        elif low[edge] > low[incoming]:
            low2[incoming] = min(low2[incoming], low[edge])
        else:
            low2[incoming] = min(low2[incoming], low2[edge])

    # Sort all edges together, then distribute them to their source vertices.
    # Sorting separately with O(n) buckets per vertex would be quadratic.
    bucket = [-1] * (2 * n)
    next_edge = [-1] * m
    for edge in range(m):
        key = nesting[edge]
        next_edge[edge] = bucket[key]
        bucket[key] = edge
    outgoing: list[list[int]] = [[] for _ in range(n)]
    for edge in bucket:
        while edge != -1:
            outgoing[source[edge]].append(edge)
            edge = next_edge[edge]

    # A conflict pair stores (left low, left high, right low, right high).
    # Each side is a same-side interval of back edges, linked by ref; the two
    # nonempty intervals must lie on opposite sides. -1 denotes an empty end.
    conflicts: list[tuple[int, int, int, int]] = []
    ref = [-1] * m
    side = [1] * m
    low_edge = [-1] * m
    bottom = [0] * m

    def add_constraints(edge: int, incoming: int) -> bool:
        left_low = left_high = right_low = right_high = -1
        # All new return edges above the parent's lowpoint must share a side.
        while len(conflicts) > bottom[edge]:
            ll, lh, rl, rh = conflicts.pop()
            if ll != -1:
                ll, lh, rl, rh = rl, rh, ll, lh
            if ll != -1:
                return False
            if low[rl] > low[incoming]:
                if right_low == -1:
                    right_high = rh
                else:
                    ref[right_low] = rh
                right_low = rl
            else:
                ref[rl] = low_edge[incoming]

        # Earlier intervals that conflict with this edge go on the other side.
        while conflicts:
            ll, lh, rl, rh = conflicts[-1]
            if not ((lh != -1 and low[lh] > low[edge]) or (rh != -1 and low[rh] > low[edge])):
                break
            conflicts.pop()
            if rh != -1 and low[rh] > low[edge]:
                ll, lh, rl, rh = rl, rh, ll, lh
            if rh != -1 and low[rh] > low[edge]:
                return False
            if right_low != -1:
                ref[right_low] = rh
            if rl != -1:
                right_low = rl
            if left_low == -1:
                left_high = lh
            else:
                ref[left_low] = lh
            left_low = ll
        if left_low != -1 or right_low != -1:
            conflicts.append((left_low, left_high, right_low, right_high))
        return True

    cursor = [0] * n
    for root in roots:
        vertices = [root]
        while vertices:
            v = vertices[-1]
            if cursor[v] == len(outgoing[v]):
                vertices.pop()
                edge = parent[v]
                if edge == -1:
                    continue
                v = source[edge]
                # On return from a child, forget back edges ending here.
                while conflicts:
                    ll, _, rl, _ = conflicts[-1]
                    lowest = low[rl] if ll == -1 else low[ll] if rl == -1 else min(low[ll], low[rl])
                    if lowest != height[v]:
                        break
                    conflicts.pop()
                    if ll != -1:
                        side[ll] = -1
                if conflicts:
                    ll, lh, rl, rh = conflicts.pop()
                    while lh != -1 and target[lh] == v:
                        lh = ref[lh]
                    if lh == -1 and ll != -1:
                        ref[ll] = rl
                        side[ll] = -1
                        ll = -1
                    while rh != -1 and target[rh] == v:
                        rh = ref[rh]
                    if rh == -1 and rl != -1:
                        ref[rl] = ll
                        side[rl] = -1
                        rl = -1
                    conflicts.append((ll, lh, rl, rh))
                if low[edge] < height[v]:
                    _, lh, _, rh = conflicts[-1]
                    ref[edge] = lh if lh != -1 and (rh == -1 or low[lh] > low[rh]) else rh
                index = cursor[v] - 1
            else:
                index = cursor[v]
                edge = outgoing[v][index]
                cursor[v] += 1
                bottom[edge] = len(conflicts)
                w = target[edge]
                if parent[w] == edge:
                    vertices.append(w)
                    continue
                low_edge[edge] = edge
                conflicts.append((-1, -1, edge, edge))
            if low[edge] < height[v]:
                incoming = parent[v]
                if index == 0:
                    low_edge[incoming] = low_edge[edge]
                elif not add_constraints(edge, incoming):
                    return None
    if not build_embedding:
        return [], []

    # Resolve relative sides once per reference, without recursive calls.
    for edge in range(m):
        path: list[int] = []
        current = edge
        while ref[current] != -1:
            path.append(current)
            current = ref[current]
        while path:
            current = path.pop()
            side[current] *= side[ref[current]]
            ref[current] = -1
        nesting[edge] *= side[edge]

    bucket = [-1] * (4 * n)
    for edge in range(m):
        key = nesting[edge] + 2 * n
        next_edge[edge] = bucket[key]
        bucket[key] = edge
    outgoing = [[] for _ in range(n)]
    for edge in bucket:
        while edge != -1:
            outgoing[source[edge]].append(edge)
            edge = next_edge[edge]

    # Circular linked lists support constant-time insertion next to a dart.
    clockwise = [-1] * (2 * m)
    counterclockwise = [-1] * (2 * m)
    first = [-1] * n

    def insert_before(half_edge: int, anchor: int) -> None:
        previous = counterclockwise[anchor]
        clockwise[previous] = half_edge
        counterclockwise[half_edge] = previous
        clockwise[half_edge] = anchor
        counterclockwise[anchor] = half_edge

    for v, row in enumerate(outgoing):
        if not row:
            continue
        first[v] = 2 * row[0]
        for i, edge in enumerate(row):
            clockwise[2 * edge] = 2 * row[(i + 1) % len(row)]
            counterclockwise[2 * edge] = 2 * row[i - 1]

    left_ref = [-1] * n
    right_ref = [-1] * n
    cursor = [0] * n
    for root in roots:
        vertices = [root]
        while vertices:
            v = vertices[-1]
            if cursor[v] == len(outgoing[v]):
                vertices.pop()
                continue
            edge = outgoing[v][cursor[v]]
            cursor[v] += 1
            w = target[edge]
            reverse = 2 * edge + 1
            if parent[w] == edge:
                if first[w] == -1:
                    clockwise[reverse] = counterclockwise[reverse] = reverse
                else:
                    insert_before(reverse, first[w])
                first[w] = reverse
                left_ref[v] = right_ref[v] = 2 * edge
                vertices.append(w)
            elif side[edge] == 1:
                insert_before(reverse, clockwise[right_ref[w]])
            else:
                insert_before(reverse, left_ref[w])
                left_ref[w] = reverse

    # Expand a simple edge to parallel darts in opposite orders at its ends.
    rotation: list[list[int]] = [[] for _ in range(n)]
    for v in range(n):
        half_edge = first[v]
        if half_edge == -1:
            continue
        while True:
            edge = half_edge // 2
            w = target[edge] if half_edge % 2 == 0 else source[edge]
            group = groups[edge] if v < w else reversed(groups[edge])
            for original in group:
                rotation[v].append(2 * original + int(graph.edges[original][0] != v))
            half_edge = clockwise[half_edge]
            if half_edge == first[v]:
                break
    # Adjacent loop darts add a monogon in an arbitrary corner at the vertex.
    for edge, (u, v) in enumerate(graph.edges):
        if u == v:
            rotation[u].extend((2 * edge, 2 * edge + 1))
    return rotation, component
