# verification-helper: PROBLEM https://judge.yosupo.jp/problem/pow_of_formal_power_series

from cplib.mathematics.polynomial import FormalPowerSeriesMod


N, M = map(int, input().split())
A = FormalPowerSeriesMod(map(int, input().split()))

print(A ** M)