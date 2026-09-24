# Problem Statement

You are given a rooted tree with vertex `0` as the root. Each vertex has a
color. For every vertex, output how many distinct colors appear in its subtree.
The subtree of a vertex consists of the vertex itself and all of its
descendants.

## Input Format

```text
n
p_1 p_2 ... p_(n-1)
c_0 c_1 ... c_(n-1)
```

If `n = 1`, the parent line is omitted. The tree is rooted at vertex `0`, and
`p_i` is the parent of vertex `i` for `1 <= i < n`.

## Output Format

Print `n` integers separated by spaces. The `i`-th integer should be the number
of distinct colors in the subtree of vertex `i`.

## Constraints

The symbols below are configured in `config.py`. The bundled `test_runner.py`
uses `NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`. These settings are chosen
so that `naive.py` usually finishes in about 2 seconds.

- `1 <= N <= N_MAX`
- For each `i` with `1 <= i < N`, `0 <= P_i < i`
- For each `i` with `0 <= i < N`, `0 <= C_i <= COLOR_MAX`

## Notes

The bundled `naive.py` traverses each subtree independently, so its worst-case
time complexity is `O(N^2)`. Under the configurable bound, this is `O(N_MAX^2)`.
