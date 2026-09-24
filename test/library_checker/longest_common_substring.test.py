# verification-helper: PROBLEM https://judge.yosupo.jp/problem/longest_common_substring

from cplib.string.suffix import longest_common_substring


S = input()
T = input()

_, sl, sr, tl, tr = longest_common_substring(S, T)

print(sl, sr, tl, tr)