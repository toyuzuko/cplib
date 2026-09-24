# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/10/ALDS1_10_A

from cplib.algorithm.dp import fibonacci_number
from cplib.tools.fastio import FastIO


N = FastIO.read_int()

FastIO.writeln(f'{fibonacci_number(N, 1, 1)}')
