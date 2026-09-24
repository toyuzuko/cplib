# Problem Statement

Given an integer array `A`, answer static range mex queries.

For each query `(l, r)`, output the minimum non-negative integer that does not
appear in the half-open interval `A[l:r]`.

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

Output `Q` lines. The `i`-th line contains the mex of `A[l_i:r_i]`.

# Constraints

- `0 <= N <= N_MAX`
- `1 <= Q <= Q_MAX`
- `VALUE_MIN <= A_i <= N + VALUE_EXTRA`
- `0 <= l_i <= r_i <= N`

The reference checker in `naive.py` constructs a set for each query and runs in
`O(Q * (N_MAX + answer))` time.
