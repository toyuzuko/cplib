# verification-helper: PROBLEM https://judge.yosupo.jp/problem/multipoint_evaluation

from cplib.mathematics.polynomial import FormalPowerSeriesMod, multipoint_evaluation


N, M = map(int, input().split())

F = FormalPowerSeriesMod(map(int, input().split()))
X = list(map(int, input().split()))

print(*multipoint_evaluation(F, X))
