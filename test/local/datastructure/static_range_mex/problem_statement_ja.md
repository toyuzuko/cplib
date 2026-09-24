# Problem Statement

整数列 `A` に対して静的区間 mex クエリに答えてください。

各クエリ `(l, r)` について、半開区間 `A[l:r]` に出現しない最小の非負整数を出力します。

# Input Format

```text
N Q
A_0 A_1 ... A_{N-1}
l_0 r_0
l_1 r_1
...
l_{Q-1} r_{Q-1}
```

# Output Format

`Q` 行出力してください。`i` 行目には `A[l_i:r_i]` の mex を出力します。

# Constraints

- `0 <= N <= N_MAX`
- `1 <= Q <= Q_MAX`
- `VALUE_MIN <= A_i <= N + VALUE_EXTRA`
- `0 <= l_i <= r_i <= N`

参照実装 `naive.py` は各クエリで集合を作り、`O(Q * (N_MAX + answer))` 時間で動作します。
