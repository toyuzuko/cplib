# verification-helper: PROBLEM https://judge.yosupo.jp/problem/matrix_det_arbitrary_mod

from cplib.mathematics.matrix import MatrixMod
from cplib.tools.fastio import FastIO


N, MOD = FastIO.read_ints(2)
A = MatrixMod(N, N, [list(FastIO.read_ints(N)) for _ in range(N)])
A.set_mod(MOD)

FastIO.writeln(f'{A.determinant()}')