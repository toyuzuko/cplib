# verification-helper: PROBLEM https://judge.yosupo.jp/problem/sqrt_of_formal_power_series_sparse

from cplib.mathematics.polynomial import FormalPowerSeriesMod


FormalPowerSeriesMod.set_sparse_threshold(50)

N, K = map(int, input().split())

coef = [0] * N

for _ in range(K):
    i, a = map(int, input().split())
    coef[i] = a

F = FormalPowerSeriesMod(coef)

try:
    print(f'{F.sqrt()}')

except ValueError:
    print('-1')
