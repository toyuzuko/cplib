# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_mode_query

from cplib.sequence.rangestat import StaticRangeModeQuery
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()

A = list(FastIO.read_ints(N))
srq = StaticRangeModeQuery(N, A)

for _ in range(Q):
    l, r = FastIO.read_ints(2)
    mode_value, mode_count = srq.range_mode(l, r)
    FastIO.writeln(f"{mode_value} {mode_count}")
