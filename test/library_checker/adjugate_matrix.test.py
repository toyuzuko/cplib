# verification-helper: PROBLEM https://judge.yosupo.jp/problem/adjugate_matrix

from cplib.mathematics.matrix import LinearAlgebraFp
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = LinearAlgebraFp(N, N, [list(FastIO.read_ints(N)) for _ in range(N)])

FastIO.writeln(f'{A.adjugate()}')