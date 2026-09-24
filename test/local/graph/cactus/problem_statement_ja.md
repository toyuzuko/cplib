# Problem Statement

連結 cactus graph が与えられます。二重連結成分、関節点、サイクル上の距離に
関するクエリに答えてください。cactus graph とは、各辺が高々 1 つの単純
サイクルに属する無向グラフです。

## Input Format

```text
N M Q
u_0 v_0 w_0
...
u_{M-1} v_{M-1} w_{M-1}
query_0
...
query_{Q-1}
```

## Output Format

各クエリについて答えを 1 行に出力してください。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。

- `1 <= N <= N_MAX`
- `Q = Q_MAX`
- 辺重みは `1` 以上 `WEIGHT_MAX` 以下
- サイクル長は高々 `CYCLE_LEN_MAX`

## Notes

generator は既存頂点に橋または単純サイクルを貼り付けてグラフを作ります。
同梱の `naive.py` は各辺を取り除いて代替パスを探すことでサイクルを復元するため、
最悪計算量は `O(M^2 N_MAX)` です。
