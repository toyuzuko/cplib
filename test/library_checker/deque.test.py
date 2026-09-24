# verification-helper: PROBLEM https://judge.yosupo.jp/problem/deque

from cplib.tools.fastio import FastIO
from cplib.datastructure.queue import DoubleEndedQueue


Q = FastIO.read_int()

deq = DoubleEndedQueue[int]()

for _ in range(Q):
    q = FastIO.read_int()
    if q == 0:
        x = FastIO.read_int()
        deq.appendleft(x)
    elif q == 1:
        x = FastIO.read_int()
        deq.append(x)
    elif q == 2:
        deq.popleft()
    elif q == 3:
        deq.pop()
    elif q == 4:
        i = FastIO.read_int()
        FastIO.writeln(f'{deq[i]}')