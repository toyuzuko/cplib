# verification-helper: PROBLEM https://judge.yosupo.jp/problem/unionfind

from cplib.graph.linkcut import LinkCutTree
from cplib.tools.fastio import FastIO

from operator import add

N, Q = FastIO.read_ints(2)
tree = LinkCutTree(N, 0, add)

for _ in range(Q):
    t, u, v = FastIO.read_ints(3)
    if t == 0:
        if not tree.same(u, v):
            tree.link(u, v)
    else:
        FastIO.writeln(f'{int(tree.same(u, v))}')
