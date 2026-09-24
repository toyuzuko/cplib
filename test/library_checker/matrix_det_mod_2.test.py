# verification-helper: PROBLEM https://judge.yosupo.jp/problem/matrix_det_mod_2

from cplib.mathematics.matrix import MatrixBit
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

A = MatrixBit(N, N, [list(map(int, FastIO.read())) for _ in range(N)])

FastIO.writeln(f'{A.determinant()}')
