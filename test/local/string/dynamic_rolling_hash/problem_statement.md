# Problem Statement

Maintain a lowercase string under point updates and answer two query types.

- `HASH l r`: output the rolling hash of `S[l:r]`.
- `FIND P l r`: output the first index where pattern `P` occurs fully inside
  `S[l:r]`, or `-1` if there is no occurrence.

For `HASH l r`, the value is
`sum(ord(S[l + i]) * 3**i for i in range(r - l)) modulo (2**61 - 1)`.
Here `ord(c)` is the Unicode code point of `c` (for example, `ord('a') = 97`).
The hash of an empty interval is zero.

The test is designed to include searches whose only match starts at
`r - len(P)` and searches with no match.

## Input Format

```text
N Q
S
query_0
query_1
...
query_{Q-1}
```

Queries are `SET i c`, `HASH l r`, or `FIND P l r`.

## Output Format

For each `HASH` and `FIND` query, print one line with the answer.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`.

- `1 <= N <= N_MAX`
- `Q = Q_MAX`
- Every initial and updated character belongs to `ALPHABET`
- Search patterns are non-empty lowercase strings

## Notes

The bundled `naive.py` keeps the actual character list and scans search ranges
directly. Its worst-case time is `O(Q_MAX * N_MAX * N_MAX)`.
