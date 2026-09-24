# Problem Statement

長さ `N` の色列 `X` を 1 つ構成してください。

各位置 `i` と色 `c` について、位置 `i` に色 `c` を置くと `P_(i, c)` 点を
得ます。さらに、隣接する 2 要素 `(X_i, X_(i+1))` ごとに
`W_(X_i, X_(i+1))` 点を得ます。

すなわち、列 `X_1, X_2, ..., X_N` の総得点は

`sum(P_(i, X_i)) + sum(W_(X_i, X_(i+1)))`

で定義されます。

有効な色列であればどのような出力でも受理されます。local verifier は
各ケースの得点をログに出力します。得点が高いほど良い解です。

## Input Format

```text
N C
P_(1,0) P_(1,1) ... P_(1,C-1)
...
P_(N,0) P_(N,1) ... P_(N,C-1)
W_(0,0) W_(0,1) ... W_(0,C-1)
...
W_(C-1,0) W_(C-1,1) ... W_(C-1,C-1)
```

## Output Format

次の形式で 1 行出力してください。

```text
X_1 X_2 ... X_N
```

各 `X_i` は `0 <= X_i < C` を満たす必要があります。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` を使います。

- `1 <= N <= N_MAX`
- `2 <= C <= C_MAX`
- `0 <= P_(i,c) <= SCORE_MAX`
- `0 <= W_(a,b) <= SCORE_MAX`

## Notes

同梱の `score.py` は列の妥当性確認と得点計算を `O(N)` で行います。
ログ出力のために、動的計画法で厳密最適値も `O(N_MAX * C_MAX^2)` で
計算します。
