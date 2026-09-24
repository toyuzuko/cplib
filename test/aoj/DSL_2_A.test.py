# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/2/DSL_2_A

from cplib.datastructure.segtree import SegmentTree
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
INF = (1 << 31) - 1

seg = SegmentTree(N, min, INF)

for _ in range(Q):
    com, x, y = FastIO.read_ints(3)
    if com == 0:
        seg.set(x, y)
    else:
        FastIO.writeln(f'{seg.prod(x, y + 1)}')
