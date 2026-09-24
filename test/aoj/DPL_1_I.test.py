# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/1/DPL_1_I

from cplib.algorithm.knapsack import KnapsackItem, bounded_knapsack_small_values
from cplib.tools.fastio import FastIO


N, W = FastIO.read_ints(2)
items: list[KnapsackItem] = []

for _ in range(N):
    v, w, m = FastIO.read_ints(3)
    items.append(KnapsackItem(w, v, m))

FastIO.writeln(f'{bounded_knapsack_small_values(items, W)}')
