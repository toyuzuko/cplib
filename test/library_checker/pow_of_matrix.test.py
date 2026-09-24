# verification-helper: PROBLEM https://judge.yosupo.jp/problem/pow_of_matrix

from cplib.mathematics.matrix import MatrixMod
from cplib.tools.fastio import FastIO


N, K = FastIO.read_ints(2)
A = MatrixMod(N, N, [list(FastIO.read_ints(N)) for _ in range(N)])
B = A ** K

FastIO.writeln(f'{B}')
