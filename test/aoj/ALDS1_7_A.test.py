# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/7/ALDS1_7_A

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
children: list[list[int]] = [[] for _ in range(N)]
parent = [-1] * N

for _ in range(N):
    v = FastIO.read_int()
    k = FastIO.read_int()
    children[v] = list(FastIO.read_ints(k))
    for u in children[v]:
        parent[u] = v

root = parent.index(-1)
depth = [0] * N
stack = [root]
while stack:
    v = stack.pop()
    for u in reversed(children[v]):
        depth[u] = depth[v] + 1
        stack.append(u)

for v in range(N):
    if parent[v] == -1:
        kind = 'root'
    elif children[v]:
        kind = 'internal node'
    else:
        kind = 'leaf'
    FastIO.writeln(f'node {v}: parent = {parent[v]}, depth = {depth[v]}, {kind}, {children[v]}')
