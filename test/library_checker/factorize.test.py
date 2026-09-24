# verification-helper: PROBLEM https://judge.yosupo.jp/problem/factorize

from cplib.mathematics.factorization import PrimeFactor
from cplib.tools.fastio import FastIO


Q = FastIO.read_int()

for _ in range(Q):
    n = FastIO.read_int()
    f = PrimeFactor.factorize(n)
    FastIO.writeln(str(len(f)) + ' ' + ' '.join(map(str, f)))
