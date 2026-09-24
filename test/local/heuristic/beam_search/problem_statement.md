# Problem Statement

You must construct a color sequence `X` of length `N`.

For each position `i` and color `c`, choosing color `c` at position `i`
contributes `P_(i, c)` points. In addition, for each adjacent pair
`(X_i, X_(i+1))`, you gain `W_(X_i, X_(i+1))` points.

More formally, the total score of a sequence `X_1, X_2, ..., X_N` is

`sum(P_(i, X_i)) + sum(W_(X_i, X_(i+1)))`.

Your task is to output any valid sequence. The local verifier accepts every
valid sequence and records its score in the log. Higher scores are better.

## Input Format

```text
N C
P_(1,0) P_(1,1) ... P_(1,C-1)
...
P_(N,0) P_(N,1) ... P_(N,C-1)
W_(0,0) W_(0,1) ... W_(0,C-1)
...
W_(C-1,0) W_(C-1,1) ... W_(C-1,C-1)
```

## Output Format

Print one line containing `N` integers:

```text
X_1 X_2 ... X_N
```

Each `X_i` must satisfy `0 <= X_i < C`.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`.

- `1 <= N <= N_MAX`
- `2 <= C <= C_MAX`
- `0 <= P_(i,c) <= SCORE_MAX`
- `0 <= W_(a,b) <= SCORE_MAX`

## Notes

The bundled `score.py` validates a sequence and computes its score in `O(N)`.
For logging only, it also computes the exact optimum with dynamic programming
in `O(N_MAX * C_MAX^2)`.
