# Problem Statement

整数集合を互いに素な半開区間として管理します。区間の追加と削除を行い、
点、区間、個数、mex に関するクエリに答えてください。

## Input Format

```text
Q
query_0
query_1
...
query_{Q-1}
```

クエリは `ADD l r`、`REM l r`、`CON p`、`FIND p`、`LEN`、`COV`、
`GET i`、`DIS l r`、`MEX p` のいずれかです。

## Output Format

値を返す各クエリについて、答えを 1 行に出力してください。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。

- `Q = Q_MAX`
- クエリ端点は `X_MIN` 以上 `X_MAX + SPAN_MAX` 以下

## Notes

同梱の `naive.py` は被覆された各整数を明示的に保持します。最悪計算量は
`O(Q_MAX * (X_MAX - X_MIN + SPAN_MAX))` です。
