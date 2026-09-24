# verification-helper: PROBLEM https://judge.yosupo.jp/problem/range_kth_smallest

from cplib.datastructure.wavelet import WaveletMatrix
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

sx = sorted(set(A))
cx = {x: i for i, x in enumerate(sx)}

comped_arr = [cx[x] for x in A]

wm = WaveletMatrix(18)

wm.build(comped_arr)

for _ in range(Q):
    l, r, k = FastIO.read_ints(3)
    FastIO.writeln(f'{sx[wm.quantile(l, r, k)]}')