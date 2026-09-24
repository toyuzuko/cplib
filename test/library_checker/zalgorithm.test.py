# verification-helper: PROBLEM https://judge.yosupo.jp/problem/zalgorithm

from cplib.string.matching import z_algorithm


S = input()
Z = z_algorithm(S)

print(' '.join(map(str, Z)))