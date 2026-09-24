# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/3/ALDS1_3_B

from cplib.datastructure.queue import DoubleEndedQueue
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()
queue = DoubleEndedQueue[tuple[str, int]]()

for _ in range(N):
    name = FastIO.read()
    time = FastIO.read_int()
    queue.append((name, time))

elapsed = 0
while queue:
    name, time = queue.popleft()
    if time <= Q:
        elapsed += time
        FastIO.writeln(f'{name} {elapsed}')
    else:
        elapsed += Q
        queue.append((name, time - Q))
