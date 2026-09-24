# Problem Statement

You are given a rooted tree with vertex `0` as the root, and a set of marked
vertices. Construct the virtual tree of the marked vertices. The virtual tree is
the smallest tree that contains every marked vertex and every lowest common
ancestor (LCA) of two marked vertices.

For each edge in the virtual tree, output its two endpoints and its weight. The
weight is the number of edges on the unique path between those two endpoints in
the original tree.

## Input Format

```text
n k
p_1 p_2 ... p_(n-1)
v_1 v_2 ... v_k
```

If `n = 1`, the parent line is omitted. The tree is rooted at vertex `0`, and
`p_i` is the parent of vertex `i` for `1 <= i < n`.

`v_1, ..., v_k` are the marked vertices. They are all distinct.

## Output Format

Output the virtual tree in the following format:

```text
cnt
x_1 x_2 ... x_cnt
edge_cnt
u_1 v_1 w_1
...
u_edge_cnt v_edge_cnt w_edge_cnt
```

The listed vertices should be in ascending order. The edges should be written in
lexicographic order of the triples `(u, v, w)`.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`. These settings are chosen
so that `naive.py` usually finishes in about 2 seconds.

- `1 <= N <= N_MAX`
- `0 <= K <= min(N, K_MAX)`
- For each `i` with `1 <= i < N`, `0 <= P_i < i`
- For each marked vertex `v_j`, `0 <= v_j < N`
- The marked vertices are pairwise distinct

## Notes

The bundled `naive.py` computes LCAs for all marked pairs and then builds the
closure explicitly. Its worst-case time complexity is `O(K^2 N + N^2)`, which
is at most `O(K_MAX^2 N_MAX + N_MAX^2)` under the configurable bounds.
