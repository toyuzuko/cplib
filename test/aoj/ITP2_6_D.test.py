# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/6/ITP2_6_D

from cplib.algorithm.bisearch import bisect_left, bisect_right
from cplib.tools.fastio import FastIO

N = FastIO.read_int()
A = FastIO.read_ints(N)
Q = FastIO.read_int()

for _ in range(Q):
    k = FastIO.read_int()
    FastIO.writeln(f'{bisect_left(A, k)} {bisect_right(A, k)}')
