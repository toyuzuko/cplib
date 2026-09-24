# verification-helper: PROBLEM https://judge.yosupo.jp/problem/log_of_formal_power_series_sparse

from cplib.mathematics.polynomial import FormalPowerSeriesMod
from cplib.tools.fastio import FastIO


FormalPowerSeriesMod.set_sparse_threshold(50)

N, K = map(int, input().split())

coef = [0] * N

for _ in range(K):
    i, a = map(int, input().split())
    coef[i] = a

F = FormalPowerSeriesMod(coef)

FastIO.writeln(f'{F.log()}')