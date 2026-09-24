# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_inversions_query

from cplib.sequence.rangestat import OfflineStaticRangeInversionsQuery
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
queries = [(FastIO.read_int(), FastIO.read_int()) for _ in range(Q)]

solver = OfflineStaticRangeInversionsQuery(A)
for answer in solver.solve(queries):
    FastIO.writeln(f'{answer}')
