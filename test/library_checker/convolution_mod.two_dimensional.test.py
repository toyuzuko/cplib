# verification-helper: PROBLEM https://judge.yosupo.jp/problem/convolution_mod

from cplib.mathematics.convolution import ConvolutionMod
from cplib.tools.fastio import FastIO

N, M = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
B = list(FastIO.read_ints(M))

answers = ConvolutionMod.convolution2d([A], [B])[0]
FastIO.writeln(' '.join(map(str, answers)))
