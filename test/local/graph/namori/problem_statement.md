# Problem Statement

Given a connected undirected graph with `N` vertices and `N` edges, answer
queries about its unique cycle and the trees attached to that cycle. Some
queries ask for branch subtrees or branch path vertex sets.

## Input Format

```text
N Q
u_0 v_0 w_0
...
u_{N-1} v_{N-1} w_{N-1}
query_0
...
query_{Q-1}
```

## Output Format

Print one line per query.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`.

- `N_MIN <= N <= N_MAX`
- `Q = Q_MAX`
- The graph is generated as a random tree plus one extra edge
- Edge weights are between `1` and `WEIGHT_MAX`

## Notes

The bundled `naive.py` peels leaves to identify the cycle and uses direct
simulation, BFS, or Dijkstra for queries. Its worst-case time is
`O(Q_MAX * N_MAX^2)`.
