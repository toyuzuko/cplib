# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_linear_add_range_min

from cplib.datastructure.segtree import RangeLinearAddRangeMin
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)

seg = RangeLinearAddRangeMin(A)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        l, r, b, c = FastIO.read_ints(4)
        seg.range_linear_add(l, r, b, c)
    else:
        l, r = FastIO.read_ints(2)
        FastIO.writeln(f'{seg.range_min(l, r)}')
