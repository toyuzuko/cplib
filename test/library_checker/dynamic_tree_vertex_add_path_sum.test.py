# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_tree_vertex_add_path_sum

from cplib.graph.linkcut import LinkCutTree
from cplib.tools.fastio import FastIO

from operator import add


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

lct = LinkCutTree(N, 0, add)
lct.build(A)

tree: list[list[int]] = [[] for _ in range(N)]

for _ in range(N - 1):
    u, v = FastIO.read_ints(2)
    tree[u].append(v)
    tree[v].append(u)

stack = [0]
par = [-1] * N

while stack:
    v = stack.pop()
    for u in tree[v]:
        if u == par[v]: continue
        par[u] = v
        stack.append(u)

for i in range(1, N):
    lct.link(i, par[i])

for _ in range(Q):
    t = FastIO.read_int()
    if t == 0:
        u, v, w, x = FastIO.read_ints(4)
        lct.cut(u, v)
        lct.link(w, x)
    elif t == 1:
        p, x = FastIO.read_ints(2)
        lct.set(p, lct.get(p) + x)
    elif t == 2:
        u, v = FastIO.read_ints(2)
        FastIO.writeln(f'{lct.path_prod(u, v)}')
