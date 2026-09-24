# Problem Statement

文字列 `S` が与えられます。2 つの文字列処理結果を出力してください。

`Lyndon word` とは、空でない文字列であって、自分自身の真の接尾辞のどれよりも辞書順で厳密に小さいものです。`Lyndon factorization` とは、文字列を Lyndon word の列に一意に分解し、それらを辞書順で非増加になるように並べたものです。

1 つ目の結果では、`S` の Lyndon factorization の境界位置を出力します。境界を `b0, b1, ..., bk` とすると、`b0 = 0`、`bk = len(S)` であり、各 factor は `S[bi : bi+1]` です。

2 つ目の結果では、`S` のすべての循環シフトを考え、辞書順で最小となるものの開始位置のうち最小のものを出力します。

## Input Format

```text
S
```

`S` は空文字列でも構いません。

## Output Format

2 行出力してください。

1 行目には `S` の Lyndon factorization の境界位置を昇順で出力してください。

2 行目には、`S` の辞書順最小な循環シフトの開始位置を出力してください。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。これらの設定は
`naive.py` が通常 2 秒程度で終わるように選んであります。

- `0 <= |S| <= LENGTH_MAX`
- `S` の各文字は `ALPHABET` に属する

## Notes

乱数生成では、`SPECIAL_CASES` に含まれる文字列を確率 `SPECIAL_CASE_RATE` で
混ぜます。
同梱の `naive.py` は分解を全探索で検証するため、最悪計算量は `|S|` に対して
指数時間です。設定ファイルの記号で粗く書けば
`O(LENGTH_MAX * 2^LENGTH_MAX)` です。
