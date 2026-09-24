# verification-helper: PROBLEM https://judge.yosupo.jp/problem/unionfind_with_potential

from cplib.datastructure.dsu import DSUWithPotential
from cplib.tools.fastio import FastIO


MOD = 998244353

N = FastIO.read_int()
Q = FastIO.read_int()

dsu = DSUWithPotential(N, lambda x, y: (x + y) % MOD, lambda x: -x % MOD, 0)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        u = FastIO.read_int()
        v = FastIO.read_int()
        x = FastIO.read_int()
        try:
            dsu.merge(u, v, x)
            FastIO.writeln('1')
        except ValueError:
            FastIO.writeln('0')
    else:
        u = FastIO.read_int()
        v = FastIO.read_int()
        try:
            FastIO.writeln(f'{dsu.diff(u, v)}')
        except ValueError:
            FastIO.writeln('-1')
