# verification-helper: PROBLEM https://judge.yosupo.jp/problem/pow_of_matrix

from cplib.mathematics.matrix import LinearAlgebraFp
from cplib.tools.fastio import FastIO


N, K = FastIO.read_ints(2)
A = LinearAlgebraFp(N, N, [list(FastIO.read_ints(N)) for _ in range(N)])

result = A.pow_by_diagonalization(K)
if result is None:
    result = A ** K

FastIO.writeln(f'{result}')
