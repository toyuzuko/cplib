# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_add_range_min

from cplib.tools.fastio import FastIO
from cplib.datastructure.segtree import LazySegmentTree

from operator import add


MOD = 998244353

N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)

seg = LazySegmentTree(N, min, 1 << 60, add, add, 0)
seg.build(A)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        l, r, x = FastIO.read_ints(3)
        seg.range_apply(l, r, x)
    else:
        l, r = FastIO.read_ints(2)
        FastIO.writeln(f'{seg.prod(l, r)}')