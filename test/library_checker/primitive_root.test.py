# verification-helper: PROBLEM https://judge.yosupo.jp/problem/primitive_root

from cplib.mathematics.factorization import PrimeFactor
from cplib.tools.fastio import FastIO


Q = FastIO.read_int()

for _ in range(Q):
    p = FastIO.read_int()
    g = PrimeFactor.primitive_root(p)
    FastIO.writeln(str(g))