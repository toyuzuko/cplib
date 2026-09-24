# Problem Statement

Given a starting time `START`, a timeout `TIMEOUT`, and `Q` observation times
`X_1, X_2, ..., X_Q` in chronological order, report the current status of a
timer at each observation.

For each observation time `X_i`, output three values:

- `elapsed = X_i - START`
- `remaining = max(0, TIMEOUT - elapsed)`
- `timeout = 1` if `elapsed >= TIMEOUT`, otherwise `0`

## Input Format

```text
Q
START TIMEOUT
X_1 X_2 ... X_Q
```

## Output Format

Print `Q` lines.

The `i`-th line must contain `elapsed`, `remaining`, and `timeout` for
`X_i`, separated by spaces.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`. These settings are chosen
so that `naive.py` usually finishes in about 2 seconds.

- `1 <= Q <= Q_MAX`
- `0 <= START <= START_MAX`
- `0 <= TIMEOUT <= TIMEOUT_MAX`
- `START <= X_i <= TIME_MAX`
- `X_1 <= X_2 <= ... <= X_Q`

## Notes

The bundled `naive.py` evaluates each observation directly with constant-time
arithmetic, so its worst-case time is `O(Q_MAX)`.
