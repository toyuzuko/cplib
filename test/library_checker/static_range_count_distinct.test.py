# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_range_count_distinct

from cplib.datastructure.wavelet import WaveletMatrix
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

last: dict[int, int] = {}
arr: list[int] = []

for i, a in enumerate(A):
    arr.append(last.get(a, 0))
    last[a] = i + 1

wm = WaveletMatrix(20)
wm.build(arr)

for _ in range(Q):
    l, r = FastIO.read_ints(2)
    res = wm.range_freq_lt(l, r, l + 1) # 区間内の値のうち、直前の出現位置がl未満であるもの(arr[i] <= l)の個数を数えれば良い
    FastIO.writeln(f'{res}')
