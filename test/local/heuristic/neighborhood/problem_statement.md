# Problem Statement

You are given an array `A` of length `N`. Define its score as

`|A_1 - A_2| + |A_2 - A_3| + ... + |A_(N-1) - A_N|`.

Process `Q` operations of the following three types:

- `1 L R`: swap `A_L` and `A_R`
- `2`: undo the most recent type `1` operation that has not yet been undone
- `3`: output the current score

Type `2` is always valid. Indices are 1-based.

## Input Format

```text
N Q
A_1 A_2 ... A_N
op_1
op_2
...
op_Q
```

Each operation is one of the following forms:

```text
1 L R
2
3
```

## Output Format

For each operation of type `3`, output the current score on its own line, in
the order they appear.

## Constraints

The symbols below are configured in `config.py`.

- `2 <= N <= N_MAX`
- `3 <= Q <= Q_MAX`
- `-VALUE_ABS_MAX <= A_i <= VALUE_ABS_MAX`
- For every type `1` operation, `1 <= L < R <= N`
- Every type `2` operation is valid

## Notes

This local verification is designed so that the bundled property-based runner
usually finishes in about 2 seconds under the default configuration.
The reference `score.py` may recompute the whole score after each query, so its
worst-case time is `O(N_MAX * Q_MAX)`.
The bundled `verify.py` updates the affected contribution of each swap in
constant time, so its worst-case time is `O(Q_MAX)`.
