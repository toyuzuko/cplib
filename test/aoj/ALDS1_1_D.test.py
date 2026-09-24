# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/1/ALDS1_1_D

from cplib.algorithm.greedy import maximum_profit
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
R = [FastIO.read_int() for _ in range(N)]

FastIO.writeln(f'{maximum_profit(R)}')
