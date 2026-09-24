# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/1/ALDS1_1_C

from cplib.mathematics.factorization import PrimeFactor
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

answer = 0
for a in A:
    if PrimeFactor.is_prime(a):
        answer += 1
FastIO.writeln(f'{answer}')
