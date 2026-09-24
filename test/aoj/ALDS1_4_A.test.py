# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/4/ALDS1_4_A

from cplib.datastructure.hash import SafeIntegerSet
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
S = FastIO.read_ints(N)
Q = FastIO.read_int()
T = FastIO.read_ints(Q)

seen = SafeIntegerSet()
for x in S:
    seen.add(x)

answer = 0
for x in T:
    if x in seen:
        answer += 1
FastIO.writeln(f'{answer}')
