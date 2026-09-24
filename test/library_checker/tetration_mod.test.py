# verification-helper: PROBLEM https://judge.yosupo.jp/problem/tetration_mod

from cplib.mathematics.factorization import PrimeFactor
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    a, b, m = FastIO.read_ints(3)
    t = PrimeFactor.tetration(a, b, m)
    FastIO.writeln(f'{t}')