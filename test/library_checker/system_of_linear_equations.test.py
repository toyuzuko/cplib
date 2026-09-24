# verification-helper: PROBLEM https://judge.yosupo.jp/problem/system_of_linear_equations

from cplib.mathematics.matrix import LinearAlgebraFp
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)

A = LinearAlgebraFp(N, M, [list(FastIO.read_ints(M)) for _ in range(N)])
b = list(FastIO.read_ints(N))

try:
    dim, sol, vecs = A.linear_equations(b)
    FastIO.writeln(f'{dim}')
    FastIO.writeln(f'{" ".join(map(str, sol))}')
    for vec in vecs:
        FastIO.writeln(f'{" ".join(map(str, vec))}')
except ValueError:
    FastIO.writeln('-1')