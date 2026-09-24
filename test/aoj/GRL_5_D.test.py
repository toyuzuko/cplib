# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/5/GRL_5_D

from cplib.datastructure.fenwicktree import RangeAddPointGet
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
bit = RangeAddPointGet(N)

Q = FastIO.read_int()
for _ in range(Q):
    query = FastIO.read_int()
    if query == 0:
        v = FastIO.read_int()
        w = FastIO.read_int()
        l, r = hld.subtree_range(Node(v))
        bit.range_add(l, r, w)
    else:
        u = FastIO.read_int()
        FastIO.writeln(f'{bit.get(hld.id[u])}')
