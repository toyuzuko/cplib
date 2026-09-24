# Problem Statement

Given an integer array `A`, answer static range strict-majority queries.

For each query `(l, r)`, output the value that appears more than half of the
time in the half-open interval `A[l:r]`. If no such value exists, output
`NONE`.

# Input Format

```text
N Q
A_0 A_1 ... A_{N-1}
l_0 r_0
l_1 r_1
...
l_{Q-1} r_{Q-1}
```

# Output Format

Output `Q` lines. The `i`-th line contains the strict majority value of
`A[l_i:r_i]`, or `NONE`.

# Constraints

- `1 <= N <= N_MAX`
- `1 <= Q <= Q_MAX`
- `VALUE_MIN <= A_i <= VALUE_MAX`
- `0 <= l_i < r_i <= N`

The reference checker in `naive.py` counts frequencies in each query interval
and runs in `O(Q * N_MAX)` time.
