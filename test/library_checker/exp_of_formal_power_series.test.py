# verification-helper: PROBLEM https://judge.yosupo.jp/problem/exp_of_formal_power_series

from cplib.mathematics.polynomial import FormalPowerSeriesMod


N = int(input())
A = FormalPowerSeriesMod(map(int, input().split()))

print(A.exp())
