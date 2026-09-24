# verification-helper: PROBLEM https://judge.yosupo.jp/problem/runenumerate

from cplib.string.period import enumerate_runs


S = input()
runs = enumerate_runs(S)

print(len(runs))

for t, l, r in runs:
    print(t, l, r)