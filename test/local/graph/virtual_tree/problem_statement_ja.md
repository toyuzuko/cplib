# Problem Statement

根を頂点 `0` とする根付き木と、いくつかの選ばれた頂点が与えられます。
選ばれた頂点の virtual tree を構成してください。virtual tree とは、
選ばれた頂点すべてと、それらの 2 頂点ずつの LCA（最小共通祖先）をすべて
含む最小の木です。

各辺について、その 2 端点と重みを出力してください。重みは、元の木上で
その 2 端点を結ぶ唯一の経路に含まれる辺の本数です。

## Input Format

```text
n k
p_1 p_2 ... p_(n-1)
v_1 v_2 ... v_k
```

`n = 1` のときは親を与える行は省略されます。木は頂点 `0` を根とし、
`p_i` は `1 <= i < n` に対する頂点 `i` の親です。

`v_1, ..., v_k` は選ばれた頂点で、すべて相異なります。

## Output Format

次の形式で virtual tree を出力してください。

```text
cnt
x_1 x_2 ... x_cnt
edge_cnt
u_1 v_1 w_1
...
u_edge_cnt v_edge_cnt w_edge_cnt
```

頂点は昇順で出力してください。辺は三つ組 `(u, v, w)` の辞書順で
出力してください。

## Constraints

以下の記号は `config.py` で設定します。同梱の `test_runner.py` は
`NUM_CASES = 100`、`TIMEOUT_SECONDS = 2.0` で実行されます。これらの設定は
`naive.py` が通常 2 秒程度で終わるように選んであります。

- `1 <= N <= N_MAX`
- `0 <= K <= min(N, K_MAX)`
- `1 <= i < N` に対して `0 <= P_i < i`
- 各選択頂点 `v_j` について `0 <= v_j < N`
- 選択頂点は相異なる

## Notes

同梱の `naive.py` は選択頂点の全組に対して LCA を求め、その閉包を明示的に
構成します。最悪計算量は `O(K^2 N + N^2)` であり、設定ファイルの記号で
書けば `O(K_MAX^2 N_MAX + N_MAX^2)` です。
