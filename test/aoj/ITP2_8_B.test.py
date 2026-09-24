# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/8/ITP2_8_B

from cplib.tools.fastio import FastIO

Q = FastIO.read_int()
M: dict[str, int] = {}

for _ in range(Q):
    com = FastIO.read_int()
    key = FastIO.read()
    if com == 0:
        M[key] = FastIO.read_int()
    elif com == 1:
        FastIO.writeln(f'{M.get(key, 0)}')
    else:
        M.pop(key, None)
