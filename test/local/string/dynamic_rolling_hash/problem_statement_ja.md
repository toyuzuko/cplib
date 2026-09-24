# Problem Statement

英小文字列を 1 点更新しながら、2 種類のクエリに答えてください。

- `HASH l r`: `S[l:r]` の rolling hash を出力する。
- `FIND P l r`: パターン `P` が完全に `S[l:r]` の中に現れる最初の位置を
  出力し、存在しなければ `-1` を出力する。

`HASH l r` の値は、`i = 0, ..., r-l-1` に対する
`ord(S[l+i]) * 3**i` の総和を `2**61 - 1` で割った余りです。
`ord(c)` は文字のUnicodeコードポイントを表し、例えば `ord('a') = 97` です。
空区間のハッシュは0です。

このテストには、一致が `r - len(P)` から始まる場合と、一致が存在しない
場合が必ず混ざります。

## Input Format

```text
N Q
S
query_0
query_1
...
query_{Q-1}
```

クエリは `SET i c`、`HASH l r`、`FIND P l r` のいずれかです。

## Output Format

各 `HASH` と `FIND` クエリについて、答えを 1 行に出力してください。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。

- `1 <= N <= N_MAX`
- `Q = Q_MAX`
- 初期文字列と更新後の各文字は `ALPHABET` に属する
- 探索パターンは空でない英小文字列

## Notes

同梱の `naive.py` は実際の文字リストを保持し、探索範囲を直接調べます。
最悪計算量は `O(Q_MAX * N_MAX * N_MAX)` です。
