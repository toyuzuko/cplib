# verification-helper: PROBLEM https://judge.yosupo.jp/problem/convolution_mod_2_64

from cplib.mathematics.convolution import Convolution64bit


N, M = map(int, input().split())
A = list(map(int, input().split()))
B = list(map(int, input().split()))

conv = Convolution64bit.convolution(A, B)

print(*conv)