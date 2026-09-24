# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/2/DSL_2_D

from cplib.datastructure.segtree import DualSegmentTree
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
INF = (1 << 31) - 1

seg = DualSegmentTree(N, lambda f, x: f if f != INF else x, INF)

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        s, t, x = FastIO.read_ints(3)
        seg.range_apply(s, t + 1, x)
    else:
        i = FastIO.read_int()
        FastIO.writeln(f'{seg.get(i)}')
