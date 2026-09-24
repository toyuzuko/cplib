# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/4/ALDS1_4_B

from cplib.algorithm.bisearch import bisect_left
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
S = FastIO.read_ints(N)
Q = FastIO.read_int()
T = FastIO.read_ints(Q)

answer = 0
for x in T:
    i = bisect_left(S, x)
    if i < N and S[i] == x:
        answer += 1
FastIO.writeln(f'{answer}')
