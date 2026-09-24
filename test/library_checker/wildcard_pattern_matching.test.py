# verification-helper: PROBLEM https://judge.yosupo.jp/problem/wildcard_pattern_matching

from cplib.string.matching import wildcard_pattern_matching


S = input()
T = input()

result = ['1' if res else '0' for res in wildcard_pattern_matching(S, T)]

print(''.join(result))