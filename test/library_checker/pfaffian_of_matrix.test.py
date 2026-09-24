# verification-helper: PROBLEM https://judge.yosupo.jp/problem/pfaffian_of_matrix

from cplib.mathematics.matrix import LinearAlgebraFp
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = LinearAlgebraFp(2 * N, 2 * N, [list(FastIO.read_ints(2 * N)) for _ in range(2 * N)])

FastIO.writeln(f'{A.pfaffian()}')
