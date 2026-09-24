# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/3/ITP2_3_C

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)
Q = FastIO.read_int()

for _ in range(Q):
    b = FastIO.read_int()
    e = FastIO.read_int()
    k = FastIO.read_int()
    FastIO.writeln(f'{A[b:e].count(k)}')
