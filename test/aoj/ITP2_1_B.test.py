# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/1/ITP2_1_B

from cplib.tools.fastio import FastIO


Q = FastIO.read_int()
A = [0] * (2 * Q + 5)
head = Q + 2
tail = head

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        d = FastIO.read_int()
        x = FastIO.read_int()
        if d == 0:
            head -= 1
            A[head] = x
        else:
            A[tail] = x
            tail += 1
    elif com == 1:
        FastIO.writeln(f'{A[head + FastIO.read_int()]}')
    else:
        d = FastIO.read_int()
        if d == 0:
            head += 1
        else:
            tail -= 1
