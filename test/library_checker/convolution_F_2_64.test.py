# verification-helper: PROBLEM https://judge.yosupo.jp/problem/convolution_F_2_64

from cplib.mathematics.convolution import ConvolutionBinaryField64
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
M = FastIO.read_int()
A = [FastIO.read_int() for _ in range(N)]
B = [FastIO.read_int() for _ in range(M)]

FastIO.writeln(' '.join(map(str, ConvolutionBinaryField64.convolution(A, B))))
