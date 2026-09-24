# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_sum_with_upper_bound

from cplib.sequence.rangestat import StaticRangeOrderQuery
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

solver = StaticRangeOrderQuery(A, log=30)
for _ in range(Q):
    l, r, x = FastIO.read_ints(3)
    FastIO.writeln(f'{solver.count_le(l, r, x)} {solver.sum_le(l, r, x)}')
