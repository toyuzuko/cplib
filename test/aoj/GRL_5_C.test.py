# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/5/GRL_5_C

from cplib.graph import HeavyLightDecomposition, Node, Tree
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
tree = Tree(N)

for v in range(N):
    K = FastIO.read_int()
    for _ in range(K):
        c = FastIO.read_int()
        tree.add_edge(Node(v), Node(c))

tree.build(Node(0))
hld = HeavyLightDecomposition(tree)

Q = FastIO.read_int()
for _ in range(Q):
    u, v = FastIO.read_ints(2)
    FastIO.writeln(f'{hld.lca(Node(u), Node(v))}')
