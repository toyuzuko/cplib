# Problem Statement

Maintain a set of integers represented as disjoint half-open intervals. Apply
range insertions and deletions, then answer point, interval, count, and mex
queries.

## Input Format

```text
Q
query_0
query_1
...
query_{Q-1}
```

Queries are `ADD l r`, `REM l r`, `CON p`, `FIND p`, `LEN`, `COV`,
`GET i`, `DIS l r`, or `MEX p`.

## Output Format

Print one line for each query that asks for a value.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`.

- `Q = Q_MAX`
- Query endpoints are between `X_MIN` and `X_MAX + SPAN_MAX`

## Notes

The bundled `naive.py` stores every covered integer explicitly. Its worst-case
time is `O(Q_MAX * (X_MAX - X_MIN + SPAN_MAX))`.
