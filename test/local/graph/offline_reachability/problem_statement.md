# Problem Statement

Given a directed graph and reachability queries, answer whether each target
vertex is reachable from the corresponding source vertex.

# Input Format

The input is given in the following format:

```text
N M Q
u_0 v_0
u_1 v_1
...
u_{M-1} v_{M-1}
s_0 t_0
s_1 t_1
...
s_{Q-1} t_{Q-1}
```

Each edge is directed from `u_i` to `v_i`. For each query, output whether
`t_i` is reachable from `s_i`. A vertex is reachable from itself.

# Output Format

Print `Q` lines. The `i`-th line must be `1` if `t_i` is reachable from
`s_i`, and `0` otherwise.

# Constraints

- `1 <= N <= N_MAX`
- `0 <= M <= M_MAX`
- `1 <= Q <= Q_MAX`
- `0 <= u_i, v_i < N`
- `0 <= s_i, t_i < N`

The reference checker in `naive.py` answers each query by BFS in
`O(Q_MAX * (N_MAX + M_MAX))` time.
