# verification-helper: PROBLEM https://judge.yosupo.jp/problem/double_ended_priority_queue

from cplib.datastructure.queue import DoubleEndedPriorityQueue
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
S = list(FastIO.read_ints(N))

dq = DoubleEndedPriorityQueue[int]()
dq.build(S)

for _ in range(Q):
    q = FastIO.read_int()
    if q == 0:
        x = FastIO.read_int()
        dq.push(x)
    elif q == 1:
        FastIO.writeln(f'{dq.pop_min()}')
    elif q == 2:
        FastIO.writeln(f'{dq.pop_max()}')
    else:
        assert False
