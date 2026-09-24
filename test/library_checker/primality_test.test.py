# verification-helper: PROBLEM https://judge.yosupo.jp/problem/primality_test

from cplib.mathematics.factorization import PrimeFactor
from cplib.tools.fastio import FastIO


Q = FastIO.read_int()

for _ in range(Q):
    n = FastIO.read_int()
    if PrimeFactor.is_prime(n):
        FastIO.writeln('Yes')
    else:
        FastIO.writeln('No')
