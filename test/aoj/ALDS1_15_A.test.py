# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/15/ALDS1_15_A

from cplib.algorithm.greedy import greedy_coin_count
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
FastIO.writeln(f'{greedy_coin_count((25, 10, 5, 1), N)}')
