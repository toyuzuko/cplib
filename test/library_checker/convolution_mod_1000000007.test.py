# verification-helper: PROBLEM https://judge.yosupo.jp/problem/convolution_mod_1000000007

from cplib.mathematics.convolution import ConvolutionLargeIntegers


MOD = 1000000007

N, M = map(int, input().split())
A = list(map(int, input().split()))
B = list(map(int, input().split()))

conv = ConvolutionLargeIntegers.convolution(A, B, MOD)

print(*conv)