# Problem Statement

Given a static graph, output its adjacency information after building a CSR
graph.

For each vertex, output the number of outgoing arcs followed by triples
`to edge_id weight` in adjacency order.

# Input Format

```text
N M D W
edge_0
edge_1
...
edge_{M-1}
```

If `W = 0`, each edge line is `u v`. If `W = 1`, each edge line is `u v w`.
If `D = 0`, the graph is undirected and each logical edge appears in both
adjacency lists. If `D = 1`, the graph is directed.

# Output Format

Output `N` lines. The `v`-th line contains the outgoing arcs of vertex `v`.

# Constraints

- `0 <= N <= N_MAX`
- `0 <= M <= M_MAX`
- `D` is `0` or `1`
- `W` is `0` or `1`
- `0 <= u, v < N`
- `W_MIN <= w <= W_MAX`

The reference checker in `naive.py` builds ordinary adjacency lists and runs in
`O(N_MAX + M_MAX)` time.
