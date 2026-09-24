# verification-helper: PROBLEM https://judge.yosupo.jp/problem/matrix_det

from cplib.mathematics.matrix import MatrixMod
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = MatrixMod(N, N, [list(FastIO.read_ints(N)) for _ in range(N)])

FastIO.writeln(f'{A.determinant()}')