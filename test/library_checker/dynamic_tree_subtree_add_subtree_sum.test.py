# verification-helper: PROBLEM https://judge.yosupo.jp/problem/dynamic_tree_subtree_add_subtree_sum

from cplib.graph.linkcut import DynamicTreeAddTreeSum
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))

lct = DynamicTreeAddTreeSum(N)
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
        u, p, x = FastIO.read_ints(3)
        lct.reroot(p)
        lct.cut_parent(u)
        lct.tree_add(u, x)
        lct.link(u, p)
    elif t == 2:
        v, p = FastIO.read_ints(2)
        lct.reroot(p)
        lct.cut_parent(v)
        FastIO.writeln(f'{lct.tree_sum(v)}')
        lct.link(v, p)
