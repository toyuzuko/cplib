# Problem Statement

`N` 頂点 `M` 辺の重み付き無向グラフが与えられます。各頂点を `0` と `1`
の 2 つのグループのどちらかに割り当ててください。

辺 `(u, v, w)` について、両端点が異なるグループに割り当てられていれば
`w` 点を得ます。同じグループなら 0 点です。

有効な 0/1 割り当てであればどのような出力でも受理されます。local
verifier は各ケースの得点をログに出力します。得点が高いほど良い解です。

## Input Format

```text
N M
u_1 v_1 w_1
...
u_M v_M w_M
```

頂点番号は 1-indexed です。

## Output Format

次の形式で 1 行出力してください。

```text
X_1 X_2 ... X_N
```

各 `X_i` は `0` または `1` でなければなりません。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` を使います。

- `2 <= N <= N_MAX`
- `1 <= M <= min(M_MAX, N(N-1)/2)`
- `1 <= u_i < v_i <= N`
- `1 <= w_i <= WEIGHT_MAX`

## Notes

同梱の `score.py` は割り当ての妥当性確認と得点計算を `O(M)` で行います。
また、local runner は得点と、単純な上界 `sum(w_i)` に対する比もログへ
出力します。
