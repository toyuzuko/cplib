# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_chmin_chmax_add_range_sum

from cplib.datastructure.segtree import SegmentTreeBeats
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

stb = SegmentTreeBeats(N)
stb.build(A)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        l, r, b = FastIO.read_ints(3)
        stb.range_chmin(l, r, b)
    elif t == 1:
        l, r, b = FastIO.read_ints(3)
        stb.range_chmax(l, r, b)
    elif t == 2:
        l, r, b = FastIO.read_ints(3)
        stb.range_add(l, r, b)
    else:
        l, r = FastIO.read_ints(2)
        FastIO.writeln(f'{stb.range_sum(l, r)}')
