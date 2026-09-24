# Problem Statement

凸な区分線形関数 `f(x)` を管理します。
初期状態では、すべての整数 `x` に対して `f(x) = 0` です。
その後、操作列を順に適用します。
初期状態と各操作の後に、現在の最小値と固定サンプル点での値を出力します。

操作は次の通りです。

- `0 a`: `f` に `max(x - a, 0)` を加える
- `1 a`: `f` に `max(a - x, 0)` を加える
- `2 a`: `f` に `abs(x - a)` を加える
- `3 d`: `f(x)` を `f(x - d)` に置き換える
- `4 l r`: `f(x)` を `min_{x - r <= y <= x - l} f(y)` に置き換える
- `5`: `f(x)` を `min_{y <= x} f(y)` に置き換える
- `6`: `f(x)` を `min_{y >= x} f(y)` に置き換える
- `7 v`: `f` のすべての値に `v` を加える

固定サンプル点は `-6` から `6` までの整数です。

## Input Format

```text
q
op_1
op_2
...
op_q
```

各 `op_i` は上記の操作列の 1 行です。

## Output Format

`q + 1` 行を出力します。
1 行目は初期状態です。
2 行目以降は各操作後の状態です。
各行には、最小値と、`-6` から `6` までの各サンプル点での値を小さい順に並べて出力します。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。これらの設定は
`naive.py` が通常 2 秒程度で終わるように選んであります。

- `1 <= Q <= Q_MAX`
- 各操作番号は `0` から `OP_TYPE_MAX`
- 操作 `0 a`, `1 a`, `2 a`, `7 v` では
  `-VALUE_ABS_MAX <= a, v <= VALUE_ABS_MAX`
- 操作 `3 d` では `-VALUE_ABS_MAX <= d <= VALUE_ABS_MAX`
- 操作 `4 l r` では
  `WINDOW_LEFT_MIN <= l <= WINDOW_LEFT_MAX` かつ `l <= r <= WINDOW_RIGHT_MAX`

## Notes

これは、凸な区分線形関数をこれらの操作で更新するデータ構造の
ローカル検証問題です。
各操作は凸性を保ち、検証器は各ステップ後の最小値と複数のサンプル点を
比較します。
同梱の `naive.py` は整数区間 `[-BRUTE_BOUND, BRUTE_BOUND]` 上で関数値を持ち、
最も重い操作がその幅に対して二乗時間です。したがって最悪計算量は
`O(Q * BRUTE_BOUND^2)`、設定ファイルの記号で書けば
`O(Q_MAX * BRUTE_BOUND^2)` です。
