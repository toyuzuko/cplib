# Problem Statement

`N` 頂点 `N` 辺の連結無向グラフが与えられます。一意なサイクルと、その
サイクルに付随する木に関するクエリに答えてください。一部のクエリでは、枝の
部分木や枝内パスの頂点集合も答えます。

## Input Format

```text
N Q
u_0 v_0 w_0
...
u_{N-1} v_{N-1} w_{N-1}
query_0
...
query_{Q-1}
```

## Output Format

各クエリについて答えを 1 行に出力してください。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。

- `N_MIN <= N <= N_MAX`
- `Q = Q_MAX`
- グラフはランダムな木に 1 本の辺を追加して生成される
- 辺重みは `1` 以上 `WEIGHT_MAX` 以下

## Notes

同梱の `naive.py` は葉を削ってサイクルを求め、クエリごとに直接シミュレーション、
BFS、または Dijkstra を使います。最悪計算量は `O(Q_MAX * N_MAX^2)` です。
