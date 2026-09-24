# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/10/ALDS1_10_D
# verification-helper: ERROR 1e-4

from cplib.algorithm.dp import optimal_binary_search_tree_cost
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
P = [FastIO.read_float() for _ in range(N)]
Q = [FastIO.read_float() for _ in range(N + 1)]

FastIO.writeln(f'{optimal_binary_search_tree_cost(P, Q):.10f}')
