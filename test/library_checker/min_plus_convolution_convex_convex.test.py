# verification-helper: PROBLEM https://judge.yosupo.jp/problem/min_plus_convolution_convex_convex

from cplib.algorithm.dp import min_plus_convolution_convex_convex

n, m = map(int, input().split())
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(*min_plus_convolution_convex_convex(a, b))
