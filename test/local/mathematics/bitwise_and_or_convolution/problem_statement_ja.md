# Problem Statement

ビットマスクで添字付けられた 2 つの配列について、bitwise AND convolution と
bitwise OR convolution を `998244353` で割った値として求めてください。

## Input Format

```text
n
a_0 a_1 ... a_{2^n-1}
b_0 b_1 ... b_{2^n-1}
```

## Output Format

2 行出力してください。1 行目は AND convolution、2 行目は OR convolution です。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。

- `0 <= n <= N_MAX`
- `0 <= a_i, b_i <= VALUE_MAX`

## Notes

同梱の `naive.py` は全てのマスク対を直接調べる二重ループで両方の畳み込みを
検査します。最悪計算量は `O(4^N_MAX)` です。
