# verification-helper: PROBLEM https://judge.yosupo.jp/problem/matrix_product_mod_2

from cplib.mathematics.matrix import MatrixBit
from cplib.tools.fastio import FastIO


N, M, K = FastIO.read_ints(3)

A = MatrixBit(N, M, [list(map(int, FastIO.read())) for _ in range(N)])
B = MatrixBit(M, K, [list(map(int, FastIO.read())) for _ in range(M)])

C = A * B

FastIO.writeln(f'{C}')
