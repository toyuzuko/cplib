# verification-helper: PROBLEM https://judge.yosupo.jp/problem/unionfind_with_potential_non_commutative_group

from cplib.datastructure.dsu import DSUWithPotential
from cplib.tools.fastio import FastIO


MOD = 998244353

N = FastIO.read_int()
Q = FastIO.read_int()

def mul_func(x: tuple[int, int, int, int], y: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return (x[0] * y[0] + x[1] * y[2]) % MOD, (x[0] * y[1] + x[1] * y[3]) % MOD, (x[2] * y[0] + x[3] * y[2]) % MOD, (x[2] * y[1] + x[3] * y[3]) % MOD

def inv_func(x: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return x[3], 0 if x[1] == 0 else MOD - x[1], 0 if x[2] == 0 else MOD - x[2], x[0]

dsu = DSUWithPotential(N, mul_func, inv_func, (1, 0, 0, 1))

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        u = FastIO.read_int()
        v = FastIO.read_int()
        (x1, x2, x3, x4) = FastIO.read_ints(4)
        try:
            dsu.merge(u, v, (x1, x2, x3, x4))
            FastIO.writeln('1')
        except ValueError:
            FastIO.writeln('0')
    else:
        u = FastIO.read_int()
        v = FastIO.read_int()
        try:
            FastIO.writeln(' '.join(map(str, dsu.diff(u, v))))
        except ValueError:
            FastIO.writeln('-1')
