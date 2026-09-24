#!/usr/bin/env python3

from __future__ import annotations

from cplib.graph.base import Node
from cplib.graph.core import Graph
from cplib.mathematics.factorial import FactorialMod
from cplib.mathematics.factorization import PrimeFactor
from cplib.mathematics.polynomial import FormalPowerSeriesMod
from cplib.mathematics.matrix import MatrixMod
from cplib.mathematics.subset import SubsetConvolution


def _graph_adjacency_bits(graph: Graph) -> tuple[list[int], bool]:
    adj = [0] * graph.n
    has_loop = False
    for u, v in graph.edges:
        if u == v:
            has_loop = True
            continue
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    return adj, has_loop


def _independent_indicator(adj: list[int]) -> list[int]:
    n = len(adj)
    independent = [0] * (1 << n)
    independent[0] = 1
    for s in range(1, 1 << n):
        bit = s & -s
        v = bit.bit_length() - 1
        rest = s ^ bit
        independent[s] = independent[rest] & (((adj[v] & rest) == 0))
    return independent


def _independent_set_count(adj: list[int]) -> list[int]:
    n = len(adj)
    count = [0] * (1 << n)
    count[0] = 1
    for s in range(1, 1 << n):
        bit = s & -s
        v = bit.bit_length() - 1
        rest = s ^ bit
        count[s] = count[rest] + count[rest & ~adj[v]]
    return count


def _transposed_subset_convolution(bits: int, s: list[int], x: list[int], mod: int) -> list[int]:
    if not x:
        return []
    if SubsetConvolution.get_mod() != mod:
        SubsetConvolution.set_mod(mod)
    return SubsetConvolution.convolution(bits, x[::-1], s)[::-1]


def _ordinary_convolution(lhs: list[int], rhs: list[int], mod: int) -> list[int]:
    result = [0] * (len(lhs) + len(rhs) - 1)
    for i, x in enumerate(lhs):
        if x == 0:
            continue
        for j, y in enumerate(rhs):
            result[i + j] = (result[i + j] + x * y) % mod
    return result


def _chromatic_values_mod(adj: list[int], mod: int) -> list[int]:
    n = len(adj)
    if n == 0:
        return [1]
    size = 1 << n
    independent = _independent_indicator(adj)
    wt = [0] * size
    wt[-1] = 1
    s = independent[:]
    c = s[0]
    s[0] = 0
    values = [0] * (n + 1)
    values[0] = 0
    dp = wt
    for i in range(n):
        next_dp = [0] * (1 << (n - 1 - i))
        for j in range(n - i):
            left = 1 << j
            right = left << 1
            part = _transposed_subset_convolution(j, s[left:right], dp[left:right], mod)
            for k, x in enumerate(part):
                next_dp[k] = (next_dp[k] + x) % mod
        dp = next_dp
        values[i + 1] = dp[0]
    if c != 0:
        if FactorialMod.get_mod() != mod:
            FactorialMod.set_mod(mod)
        factorial = FactorialMod(n)
        g = [0] * (n + 1)
        pw = 1
        for i in range(n + 1):
            g[i] = pw * factorial.factorial_inv(i) % mod
            pw = pw * c % mod
        values = _ordinary_convolution(values, g, mod)[:n + 1]
        for i in range(n + 1):
            values[i] = values[i] * factorial.factorial(i) % mod
    return values


def _interpolate_from_consecutive_values(values: list[int], mod: int) -> FormalPowerSeriesMod:
    """Interpolate small chromatic-polynomial samples without NTT size limits.

    The general polynomial interpolator uses NTT-backed products, which can
    exceed the transform size supported by small moduli.
    """
    n = len(values) - 1
    coef = [0] * (n + 1)
    for i, y in enumerate(values):
        basis = [1]
        denom = 1
        for j in range(n + 1):
            if i == j:
                continue
            next_basis = [0] * (len(basis) + 1)
            minus_j = (-j) % mod
            for d, c in enumerate(basis):
                next_basis[d] = (next_basis[d] + c * minus_j) % mod
                next_basis[d + 1] = (next_basis[d + 1] + c) % mod
            basis = next_basis
            denom = denom * (i - j) % mod
        scale = y * pow(denom, -1, mod) % mod
        for d, c in enumerate(basis):
            coef[d] = (coef[d] + scale * c) % mod
    return FormalPowerSeriesMod(coef)


def chromatic_number(graph: Graph) -> int:
    """
    Return the chromatic number of a simple undirected graph.

    Args:
        graph: Undirected input graph.

    Returns:
        The minimum number of colors needed for a proper vertex coloring.
        If the graph contains a self-loop, returns ``-1``.

    Raises:
        ValueError: If ``graph`` is directed.

    Time Complexity:
        - ``O(n 2^n)``

    Space Complexity:
        - ``O(2^n)``
    """
    if graph.is_directed:
        raise ValueError('chromatic_number is only defined for undirected graphs')
    adj, has_loop = _graph_adjacency_bits(graph)
    if has_loop:
        return -1
    n = graph.n
    if n == 0:
        return 0
    size = 1 << n
    independent = _independent_set_count(adj)
    parity = [0] * size
    for s in range(1, size):
        parity[s] = parity[s >> 1] ^ (s & 1)
    mods = (998244353, 1000000007, 1000000009)
    powers = [[1] * size for _ in mods]
    signs = [[1 if ((n ^ parity[s]) & 1) == 0 else mod - 1 for s in range(size)] for mod in mods]
    for k in range(1, n + 1):
        any_nonzero = False
        for idx, mod in enumerate(mods):
            total = 0
            power = powers[idx]
            sign = signs[idx]
            for s in range(size):
                power[s] = power[s] * independent[s] % mod
                total += sign[s] * power[s]
            if total % mod != 0:
                any_nonzero = True
        if any_nonzero:
            return k
    return -1


def chromatic_polynomial(graph: Graph, mod: int = 998244353) -> FormalPowerSeriesMod:
    """
    Return the chromatic polynomial coefficients modulo ``mod``.

    The returned polynomial has coefficients ``p`` such that
    ``P(G, x) = p[0] + p[1] x + ... + p[n] x^n``.

    Args:
        graph: Undirected input graph.
        mod: Prime modulus strictly greater than the number of vertices.

    Returns:
        Chromatic polynomial as ``FormalPowerSeriesMod``.
        If the graph contains a self-loop, this returns the zero polynomial.

    Raises:
        ValueError: If ``graph`` is directed, or ``mod`` is not a prime
            greater than the number of vertices.

    Time Complexity:
        - ``O(n^3 2^n)`` via subset-convolution-based power projection

    Space Complexity:
        - ``O(2^n)``
    """
    if graph.is_directed:
        raise ValueError('chromatic_polynomial is only defined for undirected graphs')
    if mod < 2 or mod <= graph.n or (mod != 998244353 and not PrimeFactor.is_prime(mod)):
        raise ValueError('mod must be a prime greater than the number of vertices')
    adj, has_loop = _graph_adjacency_bits(graph)
    if has_loop:
        if FormalPowerSeriesMod.get_mod() != mod:
            FormalPowerSeriesMod.set_mod(mod)
        return FormalPowerSeriesMod([0] * (graph.n + 1))
    if FormalPowerSeriesMod.get_mod() != mod:
        FormalPowerSeriesMod.set_mod(mod)
    values = _chromatic_values_mod(adj, mod)
    return _interpolate_from_consecutive_values(values, mod)


def count_spanning_trees(graph: Graph, mod: int = 998244353) -> int:
    """
    Alias for :func:`kirchhoff_theorem` to count spanning trees in an undirected graph.

    Args:
        graph: Graph object used by the algorithm.
        mod: Modulus.

    Returns:
        Number of spanning trees modulo ``mod``.

    Raises:
        ValueError: If ``graph`` is directed.

    Time Complexity:
        - ``O(n^3)``

    Space Complexity:
        - ``O(n^2)``
    """
    if graph.is_directed:
        raise ValueError('Kirchhoff\'s theorem is only applicable to undirected graphs')
    return kirchhoff_theorem(graph, mod=mod)


def count_rooted_arborescences(graph: Graph, root: Node, mod: int = 998244353) -> int:
    """
    Alias for :func:`kirchhoff_theorem` to count rooted arborescences in a directed graph.

    Args:
        graph: Directed graph.
        root: Root of the arborescence.
        mod: Modulus used for counting.

    Returns:
        int: Number of rooted arborescences modulo ``mod``.

    Raises:
        ValueError: If ``graph`` is undirected.

    Time Complexity:
        - ``O(n^3)``

    Space Complexity:
        - ``O(n^2)``
    """
    if not graph.is_directed:
        raise ValueError('Kirchhoff\'s theorem is only applicable to directed graphs')
    return kirchhoff_theorem(graph, root=root, mod=mod)


def kirchhoff_theorem(graph: Graph, root: Node | None = None, mod: int = 998244353) -> int:
    """
    Count spanning trees using Kirchhoff's matrix-tree theorem.

    For undirected graphs, this returns the number of spanning trees. For
    directed graphs, it returns the number of arborescences rooted at
    ``root``.

    Args:
        graph: Input graph.
        root: Root of the arborescence when ``graph`` is directed.
        mod: Modulus used for the determinant computation.

    Returns:
        int: Number of spanning trees or rooted arborescences modulo ``mod``.

    Raises:
        ValueError: If ``graph`` is directed and ``root`` is omitted.

    Time Complexity:
        - Dominated by determinant computation: typically ``O(n^3)``

    Space Complexity:
        - ``O(n^2)``
    """

    if graph.is_directed and root is None:
        raise ValueError('The root must be specified for directed graphs')
    lap = MatrixMod(graph.n - 1, graph.n - 1)
    if lap.get_mod() != mod:
        lap.set_mod(mod)
    if graph.is_directed:
        for u, v in graph.edges:
            assert root is not None
            if u == v:
                continue
            if u == root and v == root:
                continue
            if u == root:
                lap[v - (v > root), v - (v > root)] += 1
            elif v != root:
                lap[v - (v > root), v - (v > root)] += 1
                lap[u - (u > root), v - (v > root)] -= 1
    else:
        for u, v in graph.edges:
            if u == v:
                continue
            if u == graph.n - 1 and v == graph.n - 1:
                continue
            if u == graph.n - 1:
                lap[v, v] += 1
            elif v == graph.n - 1:
                lap[u, u] += 1
            else:
                lap[u, u] += 1
                lap[v, v] += 1
                lap[u, v] -= 1
                lap[v, u] -= 1
    return lap.determinant()


def induced_subgraph(graph: Graph, vertices: list[Node]) -> Graph:
    """
    Return the subgraph induced by a subset of vertices.

    Args:
        graph: Original graph.
        vertices: Vertices to keep, in the order used for renumbering.

    Returns:
        Graph: Induced graph whose vertex ``i`` corresponds to ``vertices[i]``.
        Original edge multiplicities, self-loops, and weights are preserved.

    Time Complexity:
        - ``O(\\sum_{v \\in S} \\deg(v))``, where ``S`` is ``vertices``
    Space Complexity:
        - ``O(|S| + m_S)``, where ``m_S`` is the number of induced edges counted
          in the graph representation
    """

    induced_graph = Graph(
        len(vertices),
        is_directed=graph.is_directed,
        connectivity_check=graph.connectivity_check,
    )
    vertex_map = {v: Node(i) for i, v in enumerate(vertices)}
    seen_edges: set[int] = set()
    for v in vertices:
        for u, e in graph.graph[v]:
            if u in vertex_map and (graph.is_directed or e not in seen_edges):
                seen_edges.add(e)
                induced_graph.add_edge(vertex_map[v], vertex_map[u], graph.wt[e])
    return induced_graph


def count_eulerian_circuits(graph: Graph, mod: int = 998244353) -> int:
    """
    Alias for :func:`best_theorem` to count Eulerian circuits in a directed graph.

    Args:
        graph: Graph object used by the algorithm.
        mod: Modulus.

    Returns:
        Number of Eulerian circuits modulo ``mod``.

    Raises:
        ValueError: If ``graph`` is undirected.

    Time Complexity:
        - ``O(n^3 + m)``
    Space Complexity:
        - ``O(n^2 + m)``
    """
    return best_theorem(graph, mod)


def best_theorem(graph: Graph, mod: int = 998244353) -> int:
    """
    Count Eulerian circuits in a directed graph using the BEST theorem.

    Args:
        graph: Directed graph.
        mod: Modulus used for counting.

    Returns:
        int: Number of Eulerian circuits modulo ``mod``.

    Raises:
        ValueError: If ``graph`` is undirected.

    Time Complexity:
        - Dominated by Kirchhoff on the non-isolated subgraph: typically ``O(n^3)``

    Space Complexity:
        - ``O(n^2)``
    """

    if not graph.is_directed:
        raise ValueError('Best theorem is only applicable to directed graphs')
    indeg = [0] * graph.n
    outdeg = [0] * graph.n
    for u in range(graph.n):
        for v, _ in graph.graph[u]:
            outdeg[u] += 1
            indeg[v] += 1
    not_isolated: list[Node] = []
    for i in range(graph.n):
        if indeg[i] != outdeg[i]:
            return 0
        if indeg[i] != 0:
            not_isolated.append(Node(i))
    if not not_isolated:
        return 1
    subgraph = induced_subgraph(graph, not_isolated)
    if FactorialMod.get_mod() != mod:
        FactorialMod.set_mod(mod)
    factorial = FactorialMod(max(outdeg) - 1)
    st_count = kirchhoff_theorem(subgraph, root=Node(0), mod=mod)
    for i in range(subgraph.n):
        st_count *= factorial.factorial(outdeg[not_isolated[i]] - 1)
        st_count %= mod
    return st_count
