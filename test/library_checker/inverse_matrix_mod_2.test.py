# verification-helper: PROBLEM https://judge.yosupo.jp/problem/inverse_matrix_mod_2

from cplib.mathematics.matrix import MatrixBit
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

A = MatrixBit(N, N, [list(map(int, FastIO.read())) for _ in range(N)])

try:
    FastIO.writeln(f'{~A}')

except ValueError as e:
    FastIO.writeln('-1')
