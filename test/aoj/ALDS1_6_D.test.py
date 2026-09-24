# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/6/ALDS1_6_D

from cplib.algorithm.sort import minimum_cost_sort
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

FastIO.writeln(f'{minimum_cost_sort(A)}')
