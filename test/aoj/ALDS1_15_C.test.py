# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/15/ALDS1_15_C

from cplib.algorithm.greedy import max_non_overlapping_intervals
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
intervals = [(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

FastIO.writeln(f'{max_non_overlapping_intervals(intervals, allow_touch=False)}')
