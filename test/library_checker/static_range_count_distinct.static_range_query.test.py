# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_count_distinct

from cplib.sequence.rangestat import StaticRangeCountDistinctQuery
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

solver = StaticRangeCountDistinctQuery(A)
for _ in range(Q):
    l, r = FastIO.read_ints(2)
    FastIO.writeln(f'{solver.count_distinct(l, r)}')
