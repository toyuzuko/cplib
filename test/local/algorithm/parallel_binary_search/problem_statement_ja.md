# Problem Statement

長さ `n` の配列があり、初期値はすべて `0` です。ここに `m` 個の一点更新
と `q` 個の問い合わせが与えられます。

各更新は `(position, delta)` の形で、指定した位置に `delta` を加えます。
各問い合わせは `(l, r, target)` の形です。
問い合わせごとに、先頭から `k` 個の更新だけを適用した状態
`k = 0, 1, ..., m` を考えます。
そのとき、半開区間 `[l, r)` の総和が `target` 以上になる最小の `k` を
求めてください。
最後まで条件を満たさない場合は `m + 1` を出力します。

## Input Format

```text
n m q
position_0 delta_0
...
position_(m-1) delta_(m-1)
l_0 r_0 target_0
...
l_(q-1) r_(q-1) target_(q-1)
```

位置と添字はすべて `0`-indexed です。

## Output Format

`q` 個の整数を空白区切りで出力します。`i` 番目の整数は `i` 番目の
問い合わせに対する最小の prefix 長、または条件が一度も真にならない場合の
`m + 1` です。

## Constraints

`_MAX` で終わる記号と `TARGET_PADDING` は `config.py` で設定します。
同梱の `test_runner.py` は `NUM_CASES = 100`、
`TIMEOUT_SECONDS = 2.0` で実行されます。これらの設定は
`naive.py` が通常 2 秒程度で終わるように選んであります。

- `1 <= N <= N_MAX`
- `1 <= M <= M_MAX`
- `1 <= Q <= Q_MAX`
- 各更新について `0 <= position < N`
- 各更新について `0 <= delta <= DELTA_MAX`
- 各問い合わせについて `0 <= l < r <= N`
- `target` は区間 `[l, r)` の最終的な和を超えても、その超過分が
  `TARGET_PADDING` 以下になるように生成されます

## Notes

これは更新列に対する first-true 問題です。各問い合わせの答えは、条件が
初めて真になる prefix 長です。
同梱の `naive.py` の最悪計算量は `O(QMN)` なので、設定ファイルの記号で
表すと `O(Q_MAX M_MAX N_MAX)` です。
