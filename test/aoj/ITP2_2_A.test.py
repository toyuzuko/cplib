# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/2/ITP2_2_A

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()
S: list[list[int]] = [[] for _ in range(N)]

for _ in range(Q):
    com = FastIO.read_int()
    t = FastIO.read_int()
    if com == 0:
        S[t].append(FastIO.read_int())
    elif com == 1:
        if S[t]:
            FastIO.writeln(f'{S[t][-1]}')
    else:
        if S[t]:
            S[t].pop()
