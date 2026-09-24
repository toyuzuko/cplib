# verification-helper: PROBLEM https://judge.yosupo.jp/problem/discrete_logarithm_mod

from cplib.mathematics.modular import discrete_logarithm
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    X, Y, M = FastIO.read_ints(3)
    FastIO.writeln(f'{discrete_logarithm(X, Y, M)}')
