# verification-helper: PROBLEM https://judge.yosupo.jp/problem/pow_of_formal_power_series_sparse

from cplib.mathematics.polynomial import FormalPowerSeriesMod


FormalPowerSeriesMod.set_sparse_threshold(50)

N, K, M = map(int, input().split())

coef = [0] * N

for _ in range(K):
    i, a = map(int, input().split())
    coef[i] = a

F = FormalPowerSeriesMod(coef)

print(F ** M)