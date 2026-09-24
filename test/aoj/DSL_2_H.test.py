# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/2/DSL_2_H

from cplib.datastructure.segtree import LazySegmentTree
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
INF = 1 << 60

seg = LazySegmentTree(N, min, INF, lambda f, x: f + x, lambda f, g: f + g, 0)
seg.build([0] * N)

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        s, t, x = FastIO.read_ints(3)
        seg.range_apply(s, t + 1, x)
    else:
        s, t = FastIO.read_ints(2)
        FastIO.writeln(f'{seg.prod(s, t + 1)}')
