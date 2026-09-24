# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_sum

from cplib.tools.fastio import FastIO
from cplib.datastructure.cumulative import Cumulative

from operator import add, sub


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

C = Cumulative(N, 0, add, sub)
C.build(A)

for _ in range(Q):
    l, r = FastIO.read_ints(2)
    x = C.prod(l, r)
    FastIO.writeln(f'{x}')