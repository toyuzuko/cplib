# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/1/ITP2_1_D

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()
A: list[list[int]] = [[] for _ in range(N)]

for _ in range(Q):
    com = FastIO.read_int()
    t = FastIO.read_int()
    if com == 0:
        A[t].append(FastIO.read_int())
    elif com == 1:
        FastIO.writeln(' '.join(map(str, A[t])))
    else:
        A[t].clear()
