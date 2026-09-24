# verification-helper: PROBLEM https://judge.yosupo.jp/problem/subset_convolution

from cplib.mathematics.subset import SubsetConvolution
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = list(FastIO.read_ints(1 << N))
B = list(FastIO.read_ints(1 << N))

res = SubsetConvolution.convolution(N, A, B)

FastIO.writeln(' '.join(map(str, res)))