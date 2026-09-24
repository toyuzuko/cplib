# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_sum_with_upper_bound

from cplib.datastructure.wavelet import WaveletMatrix
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()

A = list(FastIO.read_ints(N))

wm = WaveletMatrix(30)
wm.build(A)

for _ in range(Q):
    l = FastIO.read_int()
    r = FastIO.read_int()
    x = FastIO.read_int()
    s = wm.range_freq_lt(l, r, x + 1)
    v = wm.range_sum_lt(l, r, x + 1)
    FastIO.writeln(f'{s} {v}')
