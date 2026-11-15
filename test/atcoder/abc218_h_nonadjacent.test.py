# verification-helper: PROBLEM https://atcoder.jp/contests/abc218/tasks/abc218_h

from cplib.sequence import maximum_non_adjacent_sums
from cplib.tools.fastio import FastIO


n, r = FastIO.read_ints(2)
edges = FastIO.read_ints(n - 1)
weights = [0] * n
for i, value in enumerate(edges):
    weights[i] += value
    weights[i + 1] += value
answer = maximum_non_adjacent_sums(weights)[min(r, n - r)]
FastIO.writeln(f'{answer}')
