# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/6/ITP2_6_A

from cplib.algorithm.bisearch import bisect_left
from cplib.tools.fastio import FastIO

N = FastIO.read_int()
A = FastIO.read_ints(N)
Q = FastIO.read_int()

for _ in range(Q):
    k = FastIO.read_int()
    i = bisect_left(A, k)
    FastIO.writeln('1' if i < N and A[i] == k else '0')
