# verification-helper: PROBLEM https://judge.yosupo.jp/problem/staticrmq

from cplib.datastructure.segtree import SegmentTree
from cplib.tools.fastio import FastIO


INF = 2**31 - 1

N = FastIO.read_int()
Q = FastIO.read_int()

A = [FastIO.read_int() for _ in range(N)]

seg = SegmentTree(N, min, INF)
seg.build(A)

for _ in range(Q):
    l = FastIO.read_int()
    r = FastIO.read_int()
    FastIO.writeln(f'{seg.prod(l, r)}')
