# Problem Statement

`SM` と `XS` の 2 つの決定的な疑似乱数生成器が与えられます。`SM` は
SplitMix64 の漸化式に従い、`XS` は SplitMix64 で初期化された
xorshift128+ に従います。

最初に `SM` は `SEED_SM` で、`XS` は `SEED_XS` で初期化されます。
その後、`Q` 個のコマンドを順に処理してください。

利用できるコマンドは次の通りです。

- `SM NEXT` または `XS NEXT`
  - 選んだ生成器を 1 回進め、次の 64-bit 符号なし整数を出力します。
- `SM RANDBITS K` または `XS RANDBITS K`
  - `[0, 2^K)` の範囲から一様に選んだ整数を出力します。
- `SM RANDRANGE STOP`
  - `[0, STOP)` の範囲から一様に選んだ整数を出力します。
- `SM RANDRANGE START STOP`
  - `[START, STOP)` の範囲から一様に選んだ整数を出力します。
- `SM RANDRANGE START STOP STEP`
  - `range(START, STOP, STEP)` で表される等差数列から一様に選んだ
    整数を出力します。
- `SM RANDINT A B`
  - 区間 `[A, B]` から一様に選んだ整数を出力します。
- `SM CHOICE N X_1 ... X_N`
  - 与えられたリストから 1 要素を一様に選んで出力します。
- `SM SHUFFLE N X_1 ... X_N`
  - 与えられたリストをその場でシャッフルし、結果を出力します。

すべてのコマンドは `SM` の代わりに `XS` を使うこともできます。

## Input Format

```text
seed_sm seed_xs
q
command_0
...
command_(q-1)
```

各コマンド行は上で述べた形式のいずれかです。リストはすべて
`N` と `N` 個の整数で与えられます。

## Output Format

各コマンドについて 1 行ずつ出力してください。

- `NEXT`, `RANDBITS`, `RANDRANGE`, `RANDINT`, `CHOICE` では、得られた
  整数を出力します。
- `SHUFFLE` では、シャッフル後のリストを空白区切りで出力します。

## Constraints

以下の記号は `config.py` で設定します。同梱の runner は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。これらの
設定は、property-based verification が通常 2 秒程度で終わるように
選んであります。

- `0 <= SEED_SM <= SEED_MAX`
- `0 <= SEED_XS <= SEED_MAX`
- `1 <= Q <= Q_MAX`
- 各 `RANDBITS K` について `0 <= K <= BITS_MAX`
- 各 `RANDINT A B` について `-VALUE_ABS_MAX <= A <= B <= VALUE_ABS_MAX`
- 各 `RANDRANGE` コマンドについて、指定された範囲は空でなく、
  すべての端点は `[-VALUE_ABS_MAX, VALUE_ABS_MAX]` の範囲にある
- 各 `CHOICE` と `SHUFFLE` について `1 <= N <= LIST_MAX`
- 各リスト要素について `-VALUE_ABS_MAX <= X_i <= VALUE_ABS_MAX`

## Notes

同梱の `verify.py` と `score.py` はコマンドを順に処理します。設定ファイル
の記号で表した粗い最悪計算量は、1 ケースあたり
`O(Q_MAX * max(BITS_MAX, LIST_MAX))` です。
また、verifier は固定した seed で `random()` ヘルパーも直接検査します。
