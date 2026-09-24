# verification-helper: PROBLEM https://judge.yosupo.jp/problem/system_of_linear_equations_mod_2

from cplib.mathematics.matrix import MatrixBit
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)

A = MatrixBit(N, M, [list(map(int, FastIO.read())) for _ in range(N)])
B = list(map(int, FastIO.read()))

try:
    R, C, D = A.linear_equations(B)
    FastIO.writeln(f'{R}')
    FastIO.writeln(''.join(map(str, C)))
    for d in D:
        FastIO.writeln(''.join(map(str, d)))

except ValueError:
    FastIO.writeln('-1')
