# Problem Statement

functional graph が与えられます。歩行とサイクル分解に関するクエリに答えて
ください。各頂点はちょうど 1 本の出辺を持ちます。

クエリには、`k` ステップ後の頂点、最初の `k` ステップに沿った頂点値または
辺値の和、サイクル id、サイクル長、サイクルまでの距離、サイクル上かどうか、
サイクルへの入口が含まれます。

## Input Format

```text
N Q
to_0 to_1 ... to_{N-1}
vertex_value_0 ... vertex_value_{N-1}
edge_value_0 ... edge_value_{N-1}
query_0
query_1
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
- `0 <= to_i < N`
- `0 <= k <= K_MAX`
- 値は `0` 以上 `VALUE_MAX` 以下

## Notes

同梱の `naive.py` は歩行を直接シミュレーションし、葉を削る方法でサイクル
分解を作ります。最悪計算量は `O(N_MAX + Q_MAX * K_MAX)` です。
