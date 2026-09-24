# verification-helper: PROBLEM https://judge.yosupo.jp/problem/polynomial_taylor_shift

from cplib.mathematics.polynomial import FormalPowerSeriesMod, polynomial_shift


N, C = map(int, input().split())
A = FormalPowerSeriesMod(map(int, input().split()))

print(polynomial_shift(A, C))
