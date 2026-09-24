# Problem Statement

You are maintaining a convex piecewise-linear function `f(x)`.
Initially, `f(x) = 0` for every integer `x`.
Then you apply a sequence of operations.
After the initial state and after each operation, output the current minimum
value of `f` and the values of `f(x)` at fixed sample points.

The operations are:

- `0 a`: add `max(x - a, 0)` to `f`
- `1 a`: add `max(a - x, 0)` to `f`
- `2 a`: add `abs(x - a)` to `f`
- `3 d`: replace `f(x)` with `f(x - d)`
- `4 l r`: replace `f(x)` with `min_{x - r <= y <= x - l} f(y)`
- `5`: replace `f(x)` with `min_{y <= x} f(y)`
- `6`: replace `f(x)` with `min_{y >= x} f(y)`
- `7 v`: add `v` to every value of `f`

The sample points are the integers from `-6` to `6`.

## Input Format

```text
q
op_1
op_2
...
op_q
```

Each `op_i` is one of the operation lines above.

## Output Format

Print `q + 1` lines.
The first line is the initial state.
Each later line is the state after the corresponding operation.
Each line contains the minimum value followed by `f(x)` for every sample point
from `-6` to `6`, in increasing order.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`. These settings are chosen
so that `naive.py` usually finishes in about 2 seconds.

- `1 <= Q <= Q_MAX`
- Each operation type is an integer from `0` to `OP_TYPE_MAX`
- In operations `0 a`, `1 a`, `2 a`, and `7 v`,
  `-VALUE_ABS_MAX <= a, v <= VALUE_ABS_MAX`
- In operation `3 d`, `-VALUE_ABS_MAX <= d <= VALUE_ABS_MAX`
- In operation `4 l r`,
  `WINDOW_LEFT_MIN <= l <= WINDOW_LEFT_MAX` and `l <= r <= WINDOW_RIGHT_MAX`

## Notes

This is a local verification problem for a data structure that maintains a
convex piecewise-linear function under these operations.
The operations preserve convexity, and the verifier checks the minimum value
and several sample points after every step.
The bundled `naive.py` works on the integer interval `[-BRUTE_BOUND, BRUTE_BOUND]`
and its heaviest operation is quadratic in that width, so the overall worst-case
time is `O(Q * BRUTE_BOUND^2)`. Under the configurable bounds, this is
`O(Q_MAX * BRUTE_BOUND^2)`.
