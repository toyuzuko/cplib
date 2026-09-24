# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_affine_range_sum

from cplib.tools.fastio import FastIO
from cplib.datastructure.segtree import RangeAffineRangeSum


MOD = 998244353

N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)

seg = RangeAffineRangeSum(N, lambda: MOD)
seg.build(A)

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        l, r, b, c = FastIO.read_ints(4)
        seg.range_affine(l, r, b, c)
    else:
        l, r = FastIO.read_ints(2)
        FastIO.writeln(f'{seg.range_sum(l, r)}')