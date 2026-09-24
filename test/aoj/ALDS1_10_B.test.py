# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/10/ALDS1_10_B

from cplib.algorithm.dp import matrix_chain_multiplication_cost
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
dimensions = [(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

FastIO.writeln(f'{matrix_chain_multiplication_cost(dimensions)}')
