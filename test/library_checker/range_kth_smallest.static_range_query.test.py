# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_kth_smallest

from cplib.sequence.rangestat import StaticRangeOrderQuery
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

solver = StaticRangeOrderQuery(A, log=30)
for _ in range(Q):
    l, r, k = FastIO.read_ints(3)
    FastIO.writeln(f'{solver.kth_smallest(l, r, k)}')
