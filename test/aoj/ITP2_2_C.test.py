# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/2/ITP2_2_C

from cplib.datastructure.queue import PriorityQueue
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()
queues = [PriorityQueue[int](ascending=False) for _ in range(N)]

for _ in range(Q):
    com = FastIO.read_int()
    t = FastIO.read_int()
    queue = queues[t]
    if com == 0:
        queue.push(FastIO.read_int())
    elif com == 1:
        if queue:
            FastIO.writeln(f'{queue.top()}')
    else:
        if queue:
            queue.pop()
