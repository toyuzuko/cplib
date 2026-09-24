# Problem Statement

Given a string `S`, output two string-processing results.

A `Lyndon word` is a non-empty string that is strictly smaller in lexicographic order than every proper suffix of itself. A `Lyndon factorization` is the unique decomposition of a string into Lyndon words arranged in non-increasing lexicographic order.

For the first result, print the boundary positions of the Lyndon factorization of `S`. If the boundaries are `b0, b1, ..., bk`, then `b0 = 0`, `bk = len(S)`, and each factor is `S[bi : bi+1]`.

For the second result, consider all cyclic rotations of `S`. Output the smallest starting index among the lexicographically minimum rotations.

## Input Format

```text
S
```

`S` may be empty.

## Output Format

Print two lines.

The first line must contain the Lyndon factorization boundaries of `S` in increasing order.

The second line must contain the starting index of a lexicographically minimum cyclic rotation of `S`.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`. These settings are chosen
so that `naive.py` usually finishes in about 2 seconds.

- `0 <= |S| <= LENGTH_MAX`
- Every character of `S` belongs to `ALPHABET`

## Notes

The random generator also injects strings from `SPECIAL_CASES` with probability
`SPECIAL_CASE_RATE`.
The bundled `naive.py` checks the factorization by exhaustive search, so its
worst-case time is exponential in `|S|`. A coarse upper bound under the
configurable length bound is `O(LENGTH_MAX * 2^LENGTH_MAX)`.
