# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_lis_query

from cplib.sequence.rangestat import StaticRangeLISQuery
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
P = list(FastIO.read_ints(N))

solver = StaticRangeLISQuery(P)
for _ in range(Q):
    l, r = FastIO.read_ints(2)
    FastIO.writeln(f'{solver.range_lis(l, r)}')
