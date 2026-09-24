# verification-helper: PROBLEM https://judge.yosupo.jp/problem/matrix_product

from cplib.mathematics.matrix import MatrixMod
from cplib.tools.fastio import FastIO


N, M, K = FastIO.read_ints(3)

A = MatrixMod(N, M, [list(FastIO.read_ints(M)) for _ in range(N)])
B = MatrixMod(M, K, [list(FastIO.read_ints(K)) for _ in range(M)])

C = A * B

FastIO.writeln(f'{C}')