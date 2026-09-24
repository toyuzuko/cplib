# Problem Statement

Given two arrays indexed by bitmasks, compute their bitwise AND convolution and
bitwise OR convolution modulo `998244353`.

## Input Format

```text
n
a_0 a_1 ... a_{2^n-1}
b_0 b_1 ... b_{2^n-1}
```

## Output Format

Print two lines. The first line is the AND convolution. The second line is the
OR convolution.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`.

- `0 <= n <= N_MAX`
- `0 <= a_i, b_i <= VALUE_MAX`

## Notes

The bundled `naive.py` checks both convolutions with a direct double loop over
all mask pairs. Its worst-case time is `O(4^N_MAX)`.
