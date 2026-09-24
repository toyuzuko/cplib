# Problem Statement

開始時刻 `START`、タイムアウト `TIMEOUT`、および時系列順に並んだ
`Q` 個の観測時刻 `X_1, X_2, ..., X_Q` が与えられます。各観測時刻での
タイマーの状態を求めてください。

各観測時刻 `X_i` について、次の 3 つを出力します。

- `elapsed = X_i - START`
- `remaining = max(0, TIMEOUT - elapsed)`
- `timeout = 1`  if `elapsed >= TIMEOUT`, otherwise `0`

## Input Format

```text
Q
START TIMEOUT
X_1 X_2 ... X_Q
```

## Output Format

`Q` 行を出力してください。

`i` 行目には、`X_i` に対応する `elapsed`, `remaining`, `timeout` を
空白区切りで出力してください。

## Constraints

以下の記号は `config.py` で設定されます。付属の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行します。これらは
`naive.py` が通常 2 秒程度で終わるように選んであります。

- `1 <= Q <= Q_MAX`
- `0 <= START <= START_MAX`
- `0 <= TIMEOUT <= TIMEOUT_MAX`
- `START <= X_i <= TIME_MAX`
- `X_1 <= X_2 <= ... <= X_Q`

## Notes

同梱の `naive.py` は各観測時刻を定数時間の算術で直接処理するため、
最悪計算量は `O(Q_MAX)` です。
