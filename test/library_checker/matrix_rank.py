# verification-helper: PROBLEM https://judge.yosupo.jp/problem/matrix_rank

from cplib.mathematics.matrix import LinearAlgebraFp
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
A = LinearAlgebraFp(N, M, [list(FastIO.read_ints(M)) for _ in range(N)])

FastIO.writeln(f'{A.rank()}')