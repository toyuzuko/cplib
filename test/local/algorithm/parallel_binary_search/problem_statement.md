# Problem Statement

You are given an array of length `n` initialized with zeros, `m` point updates,
and `q` queries.

Each update is a pair `(position, delta)` meaning that `delta` is added to the
given position.
Each query is a triple `(l, r, target)`.
For a query, consider applying the first `k` updates, for `k = 0, 1, ..., m`.
Your task is to find the smallest `k` such that the sum of the array on the
half-open range `[l, r)` is at least `target`.
If the condition never becomes true, output `m + 1`.

## Input Format

```text
n m q
position_0 delta_0
...
position_(m-1) delta_(m-1)
l_0 r_0 target_0
...
l_(q-1) r_(q-1) target_(q-1)
```

All positions and indices are `0`-indexed.

## Output Format

Print `q` integers separated by spaces. The `i`-th integer is the smallest
prefix length for the `i`-th query, or `m + 1` if the query never becomes
true.

## Constraints

Symbols ending with `_MAX` and `TARGET_PADDING` are configured in `config.py`.
The bundled `test_runner.py` uses `NUM_CASES = 100` and
`TIMEOUT_SECONDS = 2.0`. These settings are chosen so that `naive.py`
usually finishes in about 2 seconds.

- `1 <= N <= N_MAX`
- `1 <= M <= M_MAX`
- `1 <= Q <= Q_MAX`
- For each update, `0 <= position < N`
- For each update, `0 <= delta <= DELTA_MAX`
- For each query, `0 <= l < r <= N`
- `target` is generated so that it exceeds the final sum on `[l, r)` by at
  most `TARGET_PADDING`

## Notes

This is a first-true problem over prefixes of updates. For each query, the
answer is the first prefix length where the condition becomes true.
The bundled `naive.py` runs in `O(QMN)` time in the worst case, so under the
configurable bounds it is `O(Q_MAX M_MAX N_MAX)`.
