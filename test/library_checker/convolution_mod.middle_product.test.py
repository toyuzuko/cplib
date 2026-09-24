# verification-helper: PROBLEM https://judge.yosupo.jp/problem/convolution_mod

from cplib.mathematics.convolution import ConvolutionMod
from cplib.tools.fastio import FastIO

N, M = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
B = list(FastIO.read_ints(M))

# Padding and reversing B turn sliding dot products into ordinary convolution.
padded = [0] * (M - 1) + A + [0] * (M - 1)
answers = ConvolutionMod.middle_product(padded, B[::-1])
FastIO.writeln(' '.join(map(str, answers)))
