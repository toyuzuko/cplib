# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_sum_with_upper_bound

from cplib.datastructure.segtree import MergeSortTree
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()

A = list(FastIO.read_ints(N))

seg = MergeSortTree(N, lambda x, y: x + y, 0)
seg.build(A)

for _ in range(Q):
    l = FastIO.read_int()
    r = FastIO.read_int()
    x = FastIO.read_int()
    s, v = seg.prod_le(l, r, x)
    FastIO.writeln(f'{s} {v}')
