# verification-helper: PROBLEM https://judge.yosupo.jp/problem/division_of_polynomials

from cplib.mathematics.polynomial import FormalPowerSeriesMod


N, M = map(int, input().split())
F = FormalPowerSeriesMod(map(int, input().split()))
G = FormalPowerSeriesMod(map(int, input().split()))

Q, R = F // G, F % G

print(len(Q), len(R))
print(Q)
print(R)