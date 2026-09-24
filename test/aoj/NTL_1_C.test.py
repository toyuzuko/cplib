# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/6/NTL/1/NTL_1_C

from math import gcd

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

answer = 1
for a in A:
    answer = answer // gcd(answer, a) * a

FastIO.writeln(f'{answer}')
