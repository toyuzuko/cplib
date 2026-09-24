# Problem Statement

Given a connected cactus graph, answer queries about biconnected blocks,
articulation points, and cycle distances. A cactus graph is an undirected graph
where every edge belongs to at most one simple cycle.

## Input Format

```text
N M Q
u_0 v_0 w_0
...
u_{M-1} v_{M-1} w_{M-1}
query_0
...
query_{Q-1}
```

## Output Format

Print one line per query.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`.

- `1 <= N <= N_MAX`
- `Q = Q_MAX`
- Edge weights are between `1` and `WEIGHT_MAX`
- Cycle lengths are at most `CYCLE_LEN_MAX`

## Notes

The generator builds graphs by gluing bridges and simple cycles at existing
vertices. The bundled `naive.py` reconstructs cycles by removing each edge and
searching for the alternate path, so its worst-case time is `O(M^2 N_MAX)`.
