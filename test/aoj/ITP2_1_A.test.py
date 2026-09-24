# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/1/ITP2_1_A

from cplib.tools.fastio import FastIO


Q = FastIO.read_int()
A: list[int] = []

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        A.append(FastIO.read_int())
    elif com == 1:
        FastIO.writeln(f'{A[FastIO.read_int()]}')
    else:
        A.pop()
