# Problem Statement

長さ `N` の配列 `A` が与えられます。配列のスコアを

`|A_1 - A_2| + |A_2 - A_3| + ... + |A_(N-1) - A_N|`

と定義します。

次の 3 種類の操作を `Q` 個処理してください。

- `1 L R`: `A_L` と `A_R` を入れ替える
- `2`: まだ取り消されていない直近の type `1` 操作を 1 つ打ち消す
- `3`: 現在のスコアを出力する

type `2` は常に実行可能であることが保証されます。添字は 1-indexed です。

## Input Format

```text
N Q
A_1 A_2 ... A_N
op_1
op_2
...
op_Q
```

各操作は次のいずれかの形式です。

```text
1 L R
2
3
```

## Output Format

type `3` の操作ごとに、その時点のスコアを 1 行ずつ出力してください。

## Constraints

以下の記号は `config.py` で設定します。

- `2 <= N <= N_MAX`
- `3 <= Q <= Q_MAX`
- `-VALUE_ABS_MAX <= A_i <= VALUE_ABS_MAX`
- type `1` の各操作について `1 <= L < R <= N`
- type `2` の各操作は必ず有効

## Notes

同梱の property-based verifier は、デフォルト設定では通常 2 秒程度で
終わるようにしてあります。
参照実装の `score.py` はクエリごとに全スコアを再計算しうるため、最悪計算量
は `O(N_MAX * Q_MAX)` です。
同梱の `verify.py` は swap で影響する寄与だけを更新するため、最悪計算量は
`O(Q_MAX)` です。
