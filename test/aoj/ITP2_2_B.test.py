# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/2/ITP2_2_B

from collections import deque

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()
queues: list[deque[int]] = [deque() for _ in range(N)]

for _ in range(Q):
    com = FastIO.read_int()
    t = FastIO.read_int()
    queue = queues[t]
    if com == 0:
        queue.append(FastIO.read_int())
    elif com == 1:
        if queue:
            FastIO.writeln(f'{queue[0]}')
    else:
        if queue:
            queue.popleft()
