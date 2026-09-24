# Problem Statement

You are given an undirected weighted graph with `N` vertices and `M` edges.
You must assign each vertex to one of two groups, represented by `0` and `1`.

For an edge `(u, v, w)`, you gain `w` points if the endpoints are assigned to
different groups, and `0` points otherwise.

Your task is to output any valid 0/1 assignment. The local verifier accepts
every valid assignment and records its score in the log. Higher scores are
better.

## Input Format

```text
N M
u_1 v_1 w_1
...
u_M v_M w_M
```

The graph uses 1-based vertex indices.

## Output Format

Print one line containing `N` integers:

```text
X_1 X_2 ... X_N
```

Each `X_i` must be either `0` or `1`.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`.

- `2 <= N <= N_MAX`
- `1 <= M <= min(M_MAX, N(N-1)/2)`
- `1 <= u_i < v_i <= N`
- `1 <= w_i <= WEIGHT_MAX`

## Notes

The bundled `score.py` validates an assignment and computes its score in `O(M)`.
The local runner also logs the ratio between the achieved score and the total
edge weight `sum(w_i)`, which is a simple upper bound on the optimum.
