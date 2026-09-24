# verification-helper: PROBLEM https://judge.yosupo.jp/problem/lca

from cplib.graph import Node, SparseTableLCA, Tree
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()

tree = Tree(N)

for i in range(N - 1):
    v = FastIO.read_int()
    tree.add_edge(Node(i + 1), Node(v))

tree.build()
lca = SparseTableLCA(tree)

for _ in range(Q):
    u, v = FastIO.read_int(), FastIO.read_int()
    FastIO.writeln(f'{lca.lca(Node(u), Node(v))}')
