# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/1/DPL_1_B

from cplib.algorithm.knapsack import KnapsackItem, knapsack
from cplib.tools.fastio import FastIO


N, W = FastIO.read_ints(2)
items: list[KnapsackItem] = []

for _ in range(N):
    v, w = FastIO.read_ints(2)
    items.append(KnapsackItem(w, v, 1))

FastIO.writeln(f'{knapsack(items, W)}')
