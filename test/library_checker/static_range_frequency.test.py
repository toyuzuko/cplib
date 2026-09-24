# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_frequency

from cplib.datastructure.wavelet import WaveletMatrix
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

wm = WaveletMatrix(30)
wm.build(A)

for _ in range(Q):
    l, r, x = FastIO.read_ints(3)
    FastIO.writeln(f'{wm.range_freq(l, r, x)}')