# verification-helper: PROBLEM https://judge.yosupo.jp/problem/bitwise_xor_convolution

from cplib.mathematics.subset import BitwiseXorConvolution
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = list(FastIO.read_ints(1 << N))
B = list(FastIO.read_ints(1 << N))

C = BitwiseXorConvolution.convolution(N, A, B)

FastIO.writeln(' '.join(map(str, C)))
