#!/usr/bin/env python3

from __future__ import annotations

from collections import deque
from typing import NamedTuple, Literal, Union


class MatchingSuccess(NamedTuple):
    """
    Successful matching result.

    Attributes:
        weight: Total weight of the matching.
        edges: Matched vertex pairs. General matching solvers report original
            vertex pairs with ``u < v``; bipartite solvers report
            ``(left_vertex, right_vertex)`` in separate index spaces.
        success: Always ``True``.

    This variant is returned when the requested matching exists.
    Check ``result.success`` to distinguish success from failure. An empty
    successful matching is falsy because its length is zero.
    The matched edges are reported on original vertex indices.

    Space Complexity:
        O(k), where k is the number of matched edges.
    """
    weight: int
    edges: list[tuple[int, int]]
    success: Literal[True]

    def __len__(self) -> int:
        """
        Return the number of matched edges.

        Returns:
            Number of matched edges.

        Time Complexity:
            O(1)
        """
        return len(self.edges)


class MatchingFailure(NamedTuple):
    """
    Failed matching result.

    Attributes:
        weight: Always ``None``.
        edges: Always ``None``.
        success: Always ``False``.

    This variant is returned when the requested matching does not exist.
    It behaves like a falsy result in typical matching APIs.
    No edge information is available in this case.

    Space Complexity:
        O(1)
    """
    weight: None
    edges: None
    success: Literal[False]

    def __len__(self) -> int:
        """
        Return the number of matched edges.

        Returns:
            Always ``0``.

        Time Complexity:
            O(1)
        """
        return 0


MatchingResult = Union[MatchingSuccess, MatchingFailure]


class MaximumWeightMatching:
    """
    General weighted matching algorithm for undirected graphs.

    Implements Edmonds' blossom algorithm for finding maximum weight
    matching in general (non-bipartite) graphs.

    Reference:
        wleungBVG, https://judge.yosupo.jp/submission/54445.

    Attributes:
        n: Number of vertices in the graph (0-indexed)

    Examples:
        >>> # Create a graph with 4 vertices
        >>> matching = MaximumWeightMatching(4)
        >>> # Add edges with weights
        >>> matching.add_edge(0, 1, 5)
        >>> matching.add_edge(1, 2, 11)
        >>> matching.add_edge(2, 3, 5)
        >>> # Find maximum weight matching
        >>> result = matching.solve()
        >>> print(result.weight)
        11
        >>> print(result.edges)
        [(1, 2)]

    Args:
        n: Number of vertices.

    Complexity Notation:
        n: Number of vertices.

    Space Complexity:
        O(n^2)
    """

    inf: int = 1 << 60

    def __init__(self, n: int) -> None:
        """Initialize a general weighted matching instance.

        Args:
            n: Number of vertices in the graph (0-indexed)

        Returns:
            None.

        Raises:
            ValueError: If n is negative.

        Time Complexity:
            O(n^2)

        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n: int = n
        self.nx: int = n
        self.m: int = 2 * n + 1
        self.u: list[int] = [0] * self.m * self.m
        self.v: list[int] = [0] * self.m * self.m
        self.w: list[int] = [0] * self.m * self.m
        self.match: list[int] = [0] * self.m
        self.slack: list[int] = [0] * self.m
        self.flower: list[list[int]] = [[] for _ in range(self.m)]
        self.flower_from: list[int] = [0] * self.m * self.m
        self.label: list[int] = [0] * self.m
        self.root: list[int] = [0] * self.m
        self.par: list[int] = [0] * self.m
        self.col: list[int] = [0] * self.m
        self.vis: list[int] = [0] * self.m
        self.que: deque[int] = deque()
        self.t: int = 0
        for u in range(1, self.m):
            for v in range(1, self.m):
                self.u[u * self.m + v] = u
                self.v[u * self.m + v] = v

    def _dist(self, u: int, v: int) -> int:
        u, v = self.u[u * self.m + v], self.v[u * self.m + v]
        return self.label[u] + self.label[v] - self.w[u * self.m + v] * 2

    def add_edge(self, u: int, v: int, w: int) -> None:
        """
        Add a weighted edge between vertices u and v.

        Args:
            u: First vertex (0-indexed)
            v: Second vertex (0-indexed)
            w: Weight of the edge

        Returns:
            None.

        Raises:
            IndexError: If either vertex is outside [0, n).
            ValueError: If the edge is a self-loop.

        Notes:
            Parallel edges keep the largest weight. Non-positive edges may be
            omitted because the empty matching is allowed.

        Time Complexity:
            O(1)

        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError('vertex id out of range')
        if u == v:
            raise ValueError('self-loops are not matching edges')
        u += 1; v += 1
        self.w[u * self.m + v] = max(self.w[u * self.m + v], w)
        self.w[v * self.m + u] = max(self.w[v * self.m + u], w)

    def _update_slack(self, u: int, x: int) -> None:
        if not self.slack[x] or self._dist(u, x) < self._dist(self.slack[x], x):
            self.slack[x] = u

    def _set_slack(self, x: int) -> None:
        self.slack[x] = 0
        for u in range(1, self.n + 1):
            if self.w[u * self.m + x] > 0 and self.root[u] != x and self.col[self.root[u]] == 0:
                self._update_slack(u, x)

    def _que_push(self, x: int) -> None:
        stack = [x]
        while stack:
            x = stack.pop()
            if x <= self.n:
                self.que.append(x)
                continue
            for _, fi in enumerate(self.flower[x]):
                stack.append(fi)

    def _set_root(self, x: int, b: int) -> None:
        stack = [x]
        while stack:
            x = stack.pop()
            self.root[x] = b
            if x <= self.n:
                continue
            for _, fi in enumerate(self.flower[x]):
                stack.append(fi)

    def _get_pr(self, b: int, xr: int) -> int:
        f = self.flower[b]
        pr = f.index(xr)
        if pr % 2 == 1:
            f = self.flower[b] = f[0:1] + f[1:][::-1]
            return len(f) - pr
        else:
            return pr

    def _set_match(self, u: int, v: int) -> None:
        self.match[u] = self.v[u * self.m + v]
        if u <= self.n:
            return
        xr = self.flower_from[u * self.m + self.u[u * self.m + v]]
        pr = self._get_pr(u, xr)
        f = self.flower[u]
        for i in range(pr):
            self._set_match(f[i], f[i ^ 1])
        self._set_match(xr, v)
        self.flower[u] = f[pr:] + f[:pr]

    def _augment(self, u: int, v: int) -> None:
        xnv = self.root[self.match[u]]
        self._set_match(u, v)
        while xnv:
            self._set_match(xnv, self.root[self.par[xnv]])
            u, v = self.root[self.par[xnv]], xnv
            xnv = self.root[self.match[u]]
            self._set_match(u, v)

    def _get_lca(self, u: int, v: int) -> int:
        self.t += 1
        while u or v:
            if not u:
                u, v = v, u
                continue
            if self.vis[u] == self.t:
                return u
            self.vis[u] = self.t
            u = self.root[self.match[u]]
            if u: u = self.root[self.par[u]]
            u, v = v, u
        return 0

    def _add_blossom(self, u: int, lca: int, v: int) -> None:
        b = self.n + 1
        while b <= self.nx and self.root[b]:
            b += 1
        if b > self.nx:
            self.nx += 1
        self.label[b] = 0
        self.col[b] = 0
        self.match[b] = self.match[lca]
        f = self.flower[b] = []
        f.append(lca)
        x = u
        while x != lca:
            f.append(x)
            y = self.root[self.match[x]]
            f.append(y)
            self._que_push(y)
            x = self.root[self.par[y]]
        f = self.flower[b] = f[0:1] + f[1:][::-1]
        x = v
        while x != lca:
            f.append(x)
            y = self.root[self.match[x]]
            f.append(y)
            self._que_push(y)
            x = self.root[self.par[y]]
        self._set_root(b, b)
        for x in range(1, self.nx + 1):
            self.w[b * self.m + x] = self.w[x * self.m + b] = 0
        for x in range(1, self.n + 1):
            self.flower_from[b * self.m + x] = 0
        for _, xs in enumerate(f):
            for x in range(1, self.nx + 1):
                if self.w[b * self.m + x] == 0 or self._dist(xs, x) < self._dist(b, x):
                    self.u[b * self.m + x] = self.u[xs * self.m + x]
                    self.u[x * self.m + b] = self.u[x * self.m + xs]
                    self.v[b * self.m + x] = self.v[xs * self.m + x]
                    self.v[x * self.m + b] = self.v[x * self.m + xs]
                    self.w[b * self.m + x] = self.w[xs * self.m + x]
                    self.w[x * self.m + b] = self.w[x * self.m + xs]
            for x in range(1, self.n + 1):
                if self.flower_from[xs * self.m + x]:
                    self.flower_from[b * self.m + x] = xs
        self._set_slack(b)

    def _expand_blossom(self, b: int) -> None:
        f = self.flower[b]
        for i, fi in enumerate(f):
            self._set_root(fi, fi)
        xr = self.flower_from[b * self.m + self.u[b * self.m + self.par[b]]]
        pr = self._get_pr(b, xr)
        f = self.flower[b]
        for i in range(0, pr, 2):
            xs = f[i]
            xns = f[i + 1]
            self.par[xs] = self.u[xns * self.m + xs]
            self.col[xs] = 1
            self.col[xns] = 0
            self.slack[xs] = 0
            self._set_slack(xns)
            self._que_push(xns)
        self.col[xr] = 1
        self.par[xr] = self.par[b]
        for i in range(pr + 1, len(f)):
            xs = f[i]
            self.col[xs] = -1
            self._set_slack(xs)
        self.root[b] = 0

    def _on_found_edge(self, u: int, v: int) -> int:
        eu = self.u[u * self.m + v]
        ev = self.v[u * self.m + v]
        u = self.root[eu]
        v = self.root[ev]
        if self.col[v] == -1:
            self.par[v] = eu
            self.col[v] = 1
            nu = self.root[self.match[v]]
            self.slack[v] = self.slack[nu] = 0
            self.col[nu] = 0
            self._que_push(nu)
        elif self.col[v] == 0:
            lca = self._get_lca(u, v)
            if not lca:
                self._augment(u, v)
                self._augment(v, u)
                return 1
            else:
                self._add_blossom(u, lca, v)
        return 0

    def _matching(self) -> int:
        for i in range(self.nx + 1):
            self.col[i] = -1
            self.slack[i] = 0
        self.que.clear()
        for x in range(1, self.nx + 1):
            if self.root[x] == x and not self.match[x]:
                self.par[x] = 0
                self.col[x] = 0
                self._que_push(x)
        if not self.que:
            return 0
        while True:
            while self.que:
                u = self.que.popleft()
                if self.col[self.root[u]] == 1:
                    continue
                for v in range(1, self.n + 1):
                    if self.w[u * self.m + v] and self.root[u] != self.root[v]:
                        if self._dist(u, v) == 0:
                            if self._on_found_edge(u, v):
                                return 1
                        else:
                            self._update_slack(u, self.root[v])
            # Reaching a zero outer-vertex label is also a stopping event.
            # Use its exact bound instead of a fixed-width infinity sentinel.
            d = min(self.label[u] for u in range(1, self.n + 1) if self.col[self.root[u]] == 0)
            for b in range(self.n + 1, self.nx + 1):
                if self.root[b] == b and self.col[b] == 1:
                    d = min(d, self.label[b] // 2)
            for x in range(1, self.nx + 1):
                if self.root[x] == x and self.slack[x]:
                    if self.col[x] == -1:
                        d = min(d, self._dist(self.slack[x], x))
                    elif self.col[x] == 0:
                        d = min(d, self._dist(self.slack[x], x) // 2)
            for u in range(1, self.n + 1):
                if self.col[self.root[u]] == 0:
                    if self.label[u] <= d:
                        return 0
                    self.label[u] -= d
                elif self.col[self.root[u]] == 1:
                    self.label[u] += d
            for b in range(self.n + 1, self.nx + 1):
                if self.root[b] == b:
                    if self.col[b] == 0:
                        self.label[b] += d * 2
                    elif self.col[b] == 1:
                        self.label[b] -= d * 2
            self.que.clear()
            for x in range(1, self.nx + 1):
                if self.root[x] == x and self.slack[x] and self.root[self.slack[x]] != x and self._dist(self.slack[x], x) == 0:
                    if self._on_found_edge(self.slack[x], x):
                        return 1
            for b in range(self.n + 1, self.nx + 1):
                if self.root[b] == b and self.col[b] == 1 and self.label[b] == 0:
                    self._expand_blossom(b)

    def solve(self) -> MatchingResult:
        """
        Find the maximum weight matching.

        Each call recomputes a matching from the currently registered edges.
        Edges may be added between calls. Integer weights are unbounded;
        complexity counts arithmetic operations.

        Returns:
            MatchingResult containing the total weight and list of matched edges

        Examples:
            >>> matching = MaximumWeightMatching(4)
            >>> matching.add_edge(0, 1, 2)
            >>> matching.add_edge(1, 2, 3)
            >>> matching.add_edge(2, 3, 4)
            >>> matching.add_edge(3, 0, 1)
            >>> result = matching.solve()
            >>> print(result.weight)  # 6
            6
            >>> print(result.edges)   # [(0, 1), (2, 3)]
            [(0, 1), (2, 3)]

        Time Complexity:
            O(n^3)

        """
        ans: int = 0
        self.nx = self.n
        self.t = 0
        self.que.clear()
        for u in range(self.m):
            self.root[u] = u if u <= self.n else 0
            self.match[u] = self.label[u] = self.vis[u] = 0
            self.par[u] = self.slack[u] = self.col[u] = 0
            self.flower[u].clear()
        w_max: int = 0
        for u in range(1, self.n + 1):
            for v in range(1, self.n + 1):
                self.flower_from[u * self.m + v] = u if u == v else 0
                w_max = max(w_max, self.w[u * self.m + v])
        for u in range(1, self.n + 1):
            self.label[u] = w_max
        while self._matching():
            pass
        for u in range(1, self.n + 1):
            if self.match[u] and self.match[u] < u:
                ans += self.w[u * self.m + self.match[u]]

        edges: list[tuple[int, int]] = []
        for u in range(1, self.n + 1):
            v = self.match[u]
            if v > 0 and u < v:
                edges.append((u - 1, v - 1))

        return MatchingSuccess(weight=ans, edges=edges, success=True)


class MinimumWeightPerfectMatching:
    """
    Minimum‑weight **perfect** matching for general (non‑bipartite) graphs.

    This is a thin wrapper around :class:`MaximumWeightMatching`.  All edges are
    re‑weighted internally so that a *maximum*‑weight call on the auxiliary
    instance returns a *minimum*‑cost **perfect** matching of the original
    instance.

    Strategy:
    Let *c*ₑ ≥ 0 be the original cost on edge *e*. Denote by
    ``C = (n // 2) * max_e c_e + 1``.
    Every edge is given the transformed weight

    ``wₑ = C − cₑ``.

    * For a perfect matching *M* (|M| = n/2) we have::

          Σₑ∈M wₑ = |M|·C − Σₑ∈M cₑ

      so maximising the left side is equivalent to minimising the right side
      among perfect matchings.
    * C exceeds the total cost of any matching, so adding one more matched
      edge dominates any possible cost increase. The wrapped maximum-weight
      solver therefore first maximizes cardinality. The wrapper verifies
      that the returned matching is perfect and reports failure otherwise.

    Examples:
        >>> mwpm = MinimumWeightPerfectMatching(4)
        >>> mwpm.add_edge(0, 1, 1)
        >>> mwpm.add_edge(1, 2, 5)
        >>> mwpm.add_edge(2, 3, 1)
        >>> mwpm.add_edge(3, 0, 5)
        >>> result = mwpm.solve()
        >>> result.weight
        2
        >>> sorted(result.edges)
        [(0, 1), (2, 3)]

    Args:
        n: Number of vertices.

    Raises:
        ValueError: If n is negative or odd.

    Space Complexity:
        O(n^2 + m)

    Complexity Notation:
        n: Number of vertices.
        m: Number of edges added with ``add_edge``.
    """

    def __init__(self, n: int) -> None:
        """Initialize a minimum-weight perfect matching instance.

        Args:
            n: Non-negative even number of vertices; zero is allowed.

        Returns:
            None.

        Raises:
            ValueError: If n is negative or odd.

        Time Complexity:
            O(1)
        """
        if n < 0 or n % 2:
            raise ValueError('n must be non-negative and even')
        self.n: int = n
        self._edges: list[tuple[int, int, int]] = []  # (u, v, cost)

    def add_edge(self, u: int, v: int, cost: int) -> None:
        """
        Add an undirected edge (u, v) with non‑negative *cost* to be minimised.

        Args:
            u: First zero-based vertex index.
            v: Second zero-based vertex index.
            cost: Non-negative edge cost to minimize.

        Returns:
            None. Records the edge for solve().

        Raises:
            IndexError: If either vertex is outside [0, n).
            ValueError: If the edge is a self-loop or cost is negative.

        Time Complexity:
            O(1) amortized
        """
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise IndexError("Vertex id out of range")
        if u == v:
            raise ValueError("No self‑loops allowed in matching graph")
        if cost < 0:
            raise ValueError("Edge cost must be non‑negative")
        self._edges.append((u, v, cost))

    def solve(self) -> MatchingResult:
        """
        Compute a minimum‑weight perfect matching.

        Returns:
            Matching result. On success, ``weight`` is the total minimum cost
            and ``edges`` is the list of matched original-vertex pairs with
            ``u < v``. On failure, ``success`` is ``False``.
            With zero vertices, the empty matching succeeds with weight zero.

        Time Complexity:
            O(n^3 + m)
        """
        if self.n == 0:
            return MatchingSuccess(weight=0, edges=[], success=True)
        if not self._edges:
            return MatchingFailure(weight=None, edges=None, success=False)

        max_cost = max(c for *_, c in self._edges)
        max_sum_cost = max_cost * (self.n // 2) + 1
        gm = MaximumWeightMatching(self.n)

        for u, v, cost in self._edges:
            gm.add_edge(u, v, max_sum_cost - cost)

        result_max = gm.solve()
        matched_edge_count = len(result_max)

        if matched_edge_count * 2 != self.n:
            return MatchingFailure(weight=None, edges=None, success=False)

        assert isinstance(result_max, MatchingSuccess)
        min_cost = matched_edge_count * max_sum_cost - result_max.weight
        return MatchingSuccess(weight=min_cost, edges=result_max.edges, success=True)


class BipartiteMaximumMatching:
    """
    Maximum bipartite matching solver using augmenting path algorithm with DFS.

    Finds the maximum cardinality matching in a bipartite graph. This implementation
    uses a specialized algorithm for bipartite graphs that is more efficient than
    using general maximum flow algorithms.

    The algorithm iteratively finds augmenting paths using depth-first search (DFS)
    from all unmatched left vertices simultaneously. It maintains a forest of
    alternating trees rooted at unmatched left vertices and expands them until
    augmenting paths are found.

    Attributes:
        n1: Number of vertices in the left partition
        n2: Number of vertices in the right partition
        graph: Adjacency list for vertices in the left partition

    Examples:
        >>> # Job assignment: assign workers to jobs
        >>> bm = BipartiteMaximumMatching(3, 3)  # 3 workers, 3 jobs
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
        >>> # result.edges contains (worker, job) pairs

        >>> # Bipartite graph coloring check
        >>> bm2 = BipartiteMaximumMatching(4, 4)
        >>> # Add edges for a cycle of length 8
        >>> for i in range(4):
        ...     bm2.add_edge(i, i)
        ...     bm2.add_edge(i, (i + 1) % 4)
        >>> result2 = bm2.solve()
        >>> assert result2.weight == 4  # Perfect matching exists

    Args:
        n1: Integer parameter ``n1``.
        n2: Integer parameter ``n2``.

    Complexity Notation:
        n1: Number of vertices in the left partition.
        n2: Number of vertices in the right partition.
        m: Number of edges added with ``add_edge``.

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
            O(n1)

        """
        if n1 < 0 or n2 < 0:
            raise ValueError('partition sizes must be non-negative')
        self.n1 = n1
        self.n2 = n2
        self.graph: list[list[int]] = [[] for _ in range(n1)]

    def add_edge(self, u: int, v: int) -> None:
        """
        Add an edge from left vertex u to right vertex v.

        Args:
            u: Vertex in the left partition (0 ≤ u < n1)
            v: Vertex in the right partition (0 ≤ v < n2)

        Returns:
            None.

        Notes:
            - Multiple edges between the same vertices are allowed but redundant
            - The graph is stored as an adjacency list for left vertices only
            - This is consistent with the BipartiteMatching API in flow.py

        Raises:
            IndexError: If either vertex is outside its partition.

        Time Complexity:
            O(1) amortized
        """
        if not (0 <= u < self.n1 and 0 <= v < self.n2):
            raise IndexError('vertex id out of range')
        self.graph[u].append(v)

    def solve(self) -> MatchingSuccess:
        """
        Find the maximum bipartite matching using DFS-based augmenting paths.

        Returns:
            MatchingSuccess containing:
            - weight: Number of edges in the maximum matching
            - edges: List of ``(left_vertex, right_vertex)`` pairs in the
              matching, with each side using its own index space
            - success: Always True (bipartite matching always has a valid result)

        Algorithm:
            The implementation uses multi-source DFS:
            1. Build a forest of alternating trees from ALL unmatched left vertices
            2. Use DFS to explore these trees simultaneously
            3. When an unmatched right vertex is found, augment along the path
            4. Continue until all trees are exhausted, then repeat

        Implementation Details:
            - pre[v]: Parent of left vertex v in the alternating tree
            - root[v]: Root of the tree containing left vertex v
            - match_l[u]: Right vertex matched to left vertex u (-1 if unmatched)
            - match_r[v]: Left vertex matched to right vertex v (-1 if unmatched)
            - Uses ~x to check if x != -1 (bitwise NOT of -1 is 0)

        Notes:
            Each successful phase increases the matching size. There are at
            most min(n1, n2) such phases, followed by one unsuccessful phase.
            The search does not restrict augmenting paths to shortest ones.

        Time Complexity:
            O((min(n1, n2) + 1) * (n1 + n2 + m)) as an upper bound.
        """
        pre = [-1] * self.n1
        root = [-1] * self.n1
        match_l = [-1] * self.n1
        match_r = [-1] * self.n2
        res = 0
        update = True
        while update:
            update = False
            stack: list[int] = []
            for i in range(self.n1):
                if not ~match_l[i]:
                    stack.append(i)
                    root[i] = i
            while stack:
                v = stack.pop()
                if ~match_l[root[v]]:
                    continue
                for c in self.graph[v]:
                    if not ~match_r[c]:
                        while ~c:
                            match_r[c] = v
                            match_l[v], c = c, match_l[v]
                            v = pre[v]
                        res += 1
                        update = True
                        break
                    c = match_r[c]
                    if not ~pre[c]:
                        pre[c] = v
                        root[c] = root[v]
                        stack.append(c)
            if update:
                pre = [-1] * self.n1
                root = [-1] * self.n1
        edges = [(i, match_l[i]) for i in range(self.n1) if ~match_l[i]]
        return MatchingSuccess(weight=res, edges=edges, success=True)


class BipartiteMinimumWeightMaximumMatching:
    """
    Minimum weight maximum bipartite matching solver using the Hungarian algorithm.

    Finds a maximum cardinality matching in a bipartite graph that minimizes the total
    weight of matched edges. This implementation uses the Hungarian algorithm (also known
    as the Kuhn-Munkres algorithm) to solve the assignment problem optimally.

    The algorithm works by:
    1. Converting the bipartite graph to a square cost matrix
    2. Applying the Hungarian algorithm to find optimal assignment
    3. Extracting valid edges that form the minimum weight maximum matching

    Attributes:
        n1: Number of vertices in the left partition
        n2: Number of vertices in the right partition
        cost_matrix: Adjacency matrix storing edge costs (inf for non-edges)
        inf: Positive infinity representing absence of an edge

    Examples:
        >>> # Task assignment: assign workers to tasks minimizing total cost
        >>> solver = BipartiteMinimumWeightMaximumMatching(3, 4)
        >>> # Worker 0 can do task 0 (cost 5) or task 1 (cost 3)
        >>> solver.add_edge(0, 0, 5)
        >>> solver.add_edge(0, 1, 3)
        >>> # Worker 1 can do task 1 (cost 2) or task 2 (cost 4)
        >>> solver.add_edge(1, 1, 2)
        >>> solver.add_edge(1, 2, 4)
        >>> # Worker 2 can do task 2 (cost 1) or task 3 (cost 6)
        >>> solver.add_edge(2, 2, 1)
        >>> solver.add_edge(2, 3, 6)
        >>>
        >>> result = solver.solve()
        >>> assert result.weight == 8  # Optimal assignment
        >>> assert len(result.edges) == 3  # All workers assigned

        >>> # Handling negative weights
        >>> solver2 = BipartiteMinimumWeightMaximumMatching(2, 2)
        >>> solver2.add_edge(0, 0, -5)  # Profit of 5
        >>> solver2.add_edge(0, 1, 3)
        >>> solver2.add_edge(1, 0, 2)
        >>> solver2.add_edge(1, 1, -2)  # Profit of 2
        >>> result2 = solver2.solve()
        >>> assert result2.weight == -7  # Total profit of 7

    Args:
        n1: Integer parameter ``n1``.
        n2: Integer parameter ``n2``.

    Complexity Notation:
        n1: Number of vertices in the left partition.
        n2: Number of vertices in the right partition.

    Space Complexity:
        O(n1 n2)
    """
    inf: float = float('inf')
    def __init__(self, n1: int, n2: int) -> None:
        """Initialize a minimum weight maximum matching solver.

        Args:
            n1: Number of vertices in the left partition (0-indexed: 0 to n1-1)
            n2: Number of vertices in the right partition (0-indexed: 0 to n2-1)

        Returns:
            None.

        Raises:
            ValueError: If either partition size is negative.

        Time Complexity:
            O(n1 * (n2 + 1))
        """
        if n1 < 0 or n2 < 0:
            raise ValueError('partition sizes must be non-negative')
        self.n1 = n1
        self.n2 = n2
        self.cost_matrix: list[list[int | float]] = [[self.inf] * n2 for _ in range(n1)]

    def add_edge(self, u: int, v: int, w: int) -> None:
        """
        Add a weighted edge from left vertex u to right vertex v.

        Args:
            u: Vertex in the left partition (0 ≤ u < n1)
            v: Vertex in the right partition (0 ≤ v < n2)
            w: Weight (cost) of the edge (can be negative)

        Returns:
            None.

        Raises:
            IndexError: If vertex indices are out of range

        Notes:
            - If multiple edges are added between the same vertices,
              the minimum weight is kept
            - Negative weights are supported and useful for profit maximization
            - The algorithm handles negative weights by applying an offset

        Time Complexity:
            O(1)
        """
        if not (0 <= u < self.n1 and 0 <= v < self.n2):
            raise IndexError("vertex id out of range")
        self.cost_matrix[u][v] = min(self.cost_matrix[u][v], w)

    def _hungarian(self, cost: list[list[int]]) -> tuple[int, list[int]]:
        n = len(cost)
        inf = n * max(map(max, cost)) + 1
        u = [0] * (n + 1)
        v = [0] * (n + 1)
        p = [0] * (n + 1)
        way = [0] * (n + 1)

        for i in range(1, n + 1):
            p[0] = i
            j0 = 0
            minv = [inf] * (n + 1)
            used = [False] * (n + 1)

            while True:
                used[j0] = True
                i0 = p[j0]
                delta = inf
                j1 = 0

                for j in range(1, n + 1):
                    if not used[j]:
                        cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                        if cur < minv[j]:
                            minv[j] = cur
                            way[j] = j0
                        if minv[j] < delta:
                            delta = minv[j]
                            j1 = j

                for j in range(n + 1):
                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta

                j0 = j1
                if p[j0] == 0:
                    break

            while True:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
                if j0 == 0:
                    break

        assign = [0] * n
        for j in range(1, n + 1):
            if p[j]:
                assign[p[j] - 1] = j - 1
        return -v[0], assign

    def solve(self) -> MatchingSuccess:
        """
        Find the minimum weight maximum bipartite matching.

        Returns:
            MatchingSuccess containing:
            - weight: Total minimum weight of the maximum matching
            - edges: List of (left_vertex, right_vertex) pairs in the matching
            - success: Always True; an empty matching is a valid solution

        Algorithm:
            The Hungarian algorithm maintains dual variables and iteratively:
            1. Finds augmenting paths in the equality subgraph
            2. Updates dual variables to create new tight edges
            3. Continues until a perfect matching is found in the square matrix

        Notes:
            - Returns maximum cardinality matching with minimum total weight
            - Handles negative weights by applying an offset
            - Graphs without edges return weight=0 and edges=[]
            - The algorithm always finds an optimal solution

        Time Complexity:
            O(max(n1, n2)^3 + n1 n2)
        """
        has_edges = False
        min_cost = 0
        max_cost = 0

        for i in range(self.n1):
            for j in range(self.n2):
                if self.cost_matrix[i][j] < self.inf:
                    has_edges = True
                    cost = int(self.cost_matrix[i][j])
                    min_cost = min(min_cost, cost)
                    max_cost = max(max_cost, cost)

        if not has_edges:
            return MatchingSuccess(weight=0, edges=[], success=True)

        offset = -min(0, min_cost)
        matrix_size = max(self.n1, self.n2)
        # One absent edge must cost more than every real edge combined.
        big_value = matrix_size * (max_cost + offset) + 1
        square_cost_matrix = [[big_value] * matrix_size for _ in range(matrix_size)]

        for i in range(self.n1):
            for j in range(self.n2):
                if self.cost_matrix[i][j] < self.inf:
                    square_cost_matrix[i][j] = int(self.cost_matrix[i][j]) + offset

        _, assign = self._hungarian(square_cost_matrix)

        edges: list[tuple[int, int]] = []
        total_cost = 0

        for u in range(self.n1):
            v = assign[u]
            if v < self.n2 and square_cost_matrix[u][v] < big_value:
                edges.append((u, v))
                total_cost += square_cost_matrix[u][v] - offset

        return MatchingSuccess(weight=total_cost, edges=edges, success=True)


class BipartiteMaximumWeightMatching:
    """
    Maximum weight bipartite matching solver using Hungarian algorithm.

    Finds a maximum-cardinality matching in a bipartite graph, breaking ties by
    maximum total weight. This is achieved by reducing the problem to minimum
    weight maximum matching with transformed weights.

    Attributes:
        n1: Number of vertices in the left partition
        n2: Number of vertices in the right partition
        weight_matrix: Adjacency matrix storing edge weights (-1 for non-edges)

    Examples:
        >>> # Profit maximization: assign workers to projects for maximum profit
        >>> solver = BipartiteMaximumWeightMatching(3, 4)
        >>> # Worker 0 on project 0 (profit 10) or project 1 (profit 15)
        >>> solver.add_edge(0, 0, 10)
        >>> solver.add_edge(0, 1, 15)
        >>> # Worker 1 on project 1 (profit 20) or project 2 (profit 5)
        >>> solver.add_edge(1, 1, 20)
        >>> solver.add_edge(1, 2, 5)
        >>> # Worker 2 on project 2 (profit 8) or project 3 (profit 12)
        >>> solver.add_edge(2, 2, 8)
        >>> solver.add_edge(2, 3, 12)
        >>>
        >>> result = solver.solve()
        >>> assert result.weight == 42  # Maximum total profit among size-3 matchings
        >>> assert len(result.edges) == 3  # All workers assigned

        >>> # Handling zero weights
        >>> solver2 = BipartiteMaximumWeightMatching(2, 2)
        >>> solver2.add_edge(0, 0, 5)
        >>> solver2.add_edge(0, 1, 0)
        >>> solver2.add_edge(1, 0, 3)
        >>> solver2.add_edge(1, 1, 0)   # Break-even
        >>> result2 = solver2.solve()
        >>> assert result2.weight == 5

    Args:
        n1: Integer parameter ``n1``.
        n2: Integer parameter ``n2``.

    Complexity Notation:
        n1: Number of vertices in the left partition.
        n2: Number of vertices in the right partition.

    Space Complexity:
        O(n1 n2)
    """
    def __init__(self, n1: int, n2: int) -> None:
        """Initialize a maximum weight bipartite matching solver.

        Args:
            n1: Number of vertices in the left partition (0-indexed: 0 to n1-1)
            n2: Number of vertices in the right partition (0-indexed: 0 to n2-1)

        Returns:
            None.

        Raises:
            ValueError: If either partition size is negative.

        Time Complexity:
            O(n1 * (n2 + 1))
        """
        if n1 < 0 or n2 < 0:
            raise ValueError('partition sizes must be non-negative')
        self.n1 = n1
        self.n2 = n2
        self.weight_matrix = [[-1] * n2 for _ in range(n1)]

    def add_edge(self, u: int, v: int, w: int) -> None:
        """
        Add a weighted edge from left vertex u to right vertex v.

        Args:
            u: Vertex in the left partition (0 ≤ u < n1)
            v: Vertex in the right partition (0 ≤ v < n2)
            w: Non-negative weight (profit/value) of the edge.

        Returns:
            None.

        Raises:
            IndexError: If vertex indices are out of range.
            ValueError: If w is negative.

        Notes:
            - If multiple edges are added between the same vertices,
              the maximum weight is kept
            - Zero weights are treated as valid edges

        Time Complexity:
            O(1)
        """
        if not (0 <= u < self.n1 and 0 <= v < self.n2):
            raise IndexError("vertex id out of range")
        if w < 0:
            raise ValueError('weight must be non-negative')
        self.weight_matrix[u][v] = max(self.weight_matrix[u][v], w)

    def solve(self) -> MatchingSuccess:
        """
        Find the maximum weight bipartite matching.

        Returns:
            MatchingSuccess containing:
            - weight: Total maximum weight of the matching
            - edges: List of (left_vertex, right_vertex) pairs in the matching
            - success: Always True; an empty matching is a valid solution

        Algorithm:
            Reduces maximum weight matching to minimum weight matching by:
            1. Transforming weights: w' = max_weight + 1 - w
            2. Solving minimum weight maximum matching on transformed weights
            3. Converting back to get maximum weight solution

        Notes:
            - The matching has maximum cardinality and then maximum total weight
            - Graphs without edges return weight=0 and edges=[]
            - Uses BipartiteMinimumWeightMaximumMatching internally

        Time Complexity:
            O(max(n1, n2)^3 + n1 n2)
        """
        has_edges = False
        max_weight = -1

        for i in range(self.n1):
            for j in range(self.n2):
                if self.weight_matrix[i][j] >= 0:
                    has_edges = True
                    max_weight = max(max_weight, self.weight_matrix[i][j])

        if not has_edges:
            return MatchingSuccess(weight=0, edges=[], success=True)

        weight_offset = max(0, max_weight) + 1

        solver = BipartiteMinimumWeightMaximumMatching(self.n1, self.n2)
        for i in range(self.n1):
            for j in range(self.n2):
                if self.weight_matrix[i][j] >= 0:
                    solver.add_edge(i, j, weight_offset - self.weight_matrix[i][j])

        res_min = solver.solve()

        total_weight = 0
        for u, v in res_min.edges:
            total_weight += self.weight_matrix[u][v]

        return MatchingSuccess(weight=total_weight, edges=res_min.edges, success=True)
