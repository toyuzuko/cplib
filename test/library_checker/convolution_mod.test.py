# verification-helper: PROBLEM https://judge.yosupo.jp/problem/convolution_mod

from cplib.mathematics.convolution import ConvolutionMod


N, M = map(int, input().split())
A = list(map(int, input().split()))
B = list(map(int, input().split()))

conv = ConvolutionMod.convolution(A, B)

print(*conv)