# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/4/ITP2_4_B

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = list(FastIO.read_ints(N))
Q = FastIO.read_int()

for _ in range(Q):
    b = FastIO.read_int()
    m = FastIO.read_int()
    e = FastIO.read_int()
    A[b:e] = A[m:e] + A[b:m]

FastIO.writeln(' '.join(map(str, A)))
