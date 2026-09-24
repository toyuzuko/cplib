# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/2/DSL_2_F

from cplib.datastructure.segtree import SegmentTreeBeats
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
INF = (1 << 31) - 1

seg = SegmentTreeBeats(N)
seg.build([INF] * N)

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        s, t, x = FastIO.read_ints(3)
        seg.range_set(s, t + 1, x)
    else:
        s, t = FastIO.read_ints(2)
        FastIO.writeln(f'{seg.range_min(s, t + 1)}')
