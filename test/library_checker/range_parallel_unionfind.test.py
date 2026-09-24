# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_parallel_unionfind

from cplib.datastructure.dsu import RangeParallelDSU
from cplib.tools.fastio import FastIO


MOD = 998244353

N = FastIO.read_int()
Q = FastIO.read_int()
X = list(FastIO.read_ints(N))


def add_mod(a: int, b: int) -> int:
    if a + b >= MOD:
        return a + b - MOD
    return a + b


def mul_mod(a: int, b: int) -> int:
    return (a * b) % MOD


dsu = RangeParallelDSU(N, X, add_mod, mul_mod, add_mod, 0)

for _ in range(Q):
    k, a, b = FastIO.read_ints(3)
    dsu.range_merge(k, a, b)
    FastIO.writeln(f'{dsu.pair_sum()}')
