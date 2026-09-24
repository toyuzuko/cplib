# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/3/ITP2_3_B

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)
Q = FastIO.read_int()

for _ in range(Q):
    com = FastIO.read_int()
    b = FastIO.read_int()
    e = FastIO.read_int()
    if com == 0:
        FastIO.writeln(f'{min(A[b:e])}')
    else:
        FastIO.writeln(f'{max(A[b:e])}')
