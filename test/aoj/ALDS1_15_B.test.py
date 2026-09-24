# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/15/ALDS1_15_B
# verification-helper: ERROR 1e-6

from cplib.algorithm.greedy import fractional_knapsack
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
W = FastIO.read_int()
items = [(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

FastIO.writeln(f'{fractional_knapsack(items, W):.10f}')
