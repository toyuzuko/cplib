# Problem Statement

Given a functional graph, answer walk and cycle-decomposition queries.
Each vertex has exactly one outgoing edge.

Queries include jumping by `k` steps, aggregating vertex or edge values over the
first `k` steps, and asking for cycle id, cycle length, distance to cycle,
cycle membership, and cycle entry.

## Input Format

```text
N Q
to_0 to_1 ... to_{N-1}
vertex_value_0 ... vertex_value_{N-1}
edge_value_0 ... edge_value_{N-1}
query_0
query_1
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
- `0 <= to_i < N`
- `0 <= k <= K_MAX`
- Values are between `0` and `VALUE_MAX`

## Notes

The bundled `naive.py` simulates walks directly and rebuilds the cycle
decomposition by leaf peeling. Its worst-case time is `O(N_MAX + Q_MAX * K_MAX)`.
