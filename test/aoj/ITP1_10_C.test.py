# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/10/ITP1_10_C
# verification-helper: ERROR 1e-6

from math import sqrt

from cplib.tools.fastio import FastIO


while True:
    n = FastIO.read_int()
    if n == 0:
        break
    S = FastIO.read_ints(n)
    mean = sum(S) / n
    variance = sum((x - mean) ** 2 for x in S) / n
    FastIO.writeln(f'{sqrt(variance):.10f}')
