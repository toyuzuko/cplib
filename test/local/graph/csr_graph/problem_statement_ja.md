# Problem Statement

静的グラフを受け取り、CSR グラフとして構築した後の隣接情報を出力してください。

各頂点について、出次数に続けて `to edge_id weight` の三つ組を隣接順に出力します。

# Input Format

```text
N M D W
edge_0
edge_1
...
edge_{M-1}
```

`W = 0` のとき各辺は `u v`、`W = 1` のとき各辺は `u v w` です。
`D = 0` のときグラフは無向で、各論理辺は両端の隣接リストに現れます。`D = 1` のときグラフは有向です。

# Output Format

`N` 行出力してください。`v` 行目には頂点 `v` の outgoing arc を出力します。

# Constraints

- `0 <= N <= N_MAX`
- `0 <= M <= M_MAX`
- `D` is `0` or `1`
- `W` is `0` or `1`
- `0 <= u, v < N`
- `W_MIN <= w <= W_MAX`

参照実装 `naive.py` は通常の隣接リストを構築し、`O(N_MAX + M_MAX)` 時間で動作します。
