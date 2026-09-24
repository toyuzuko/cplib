# verification-helper: PROBLEM https://judge.yosupo.jp/problem/lca

from cplib.graph import Tree, HeavyLightDecomposition, Node
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()

tree = Tree(N)

for i in range(N - 1):
    v = FastIO.read_int()
    tree.add_edge(Node(i + 1), Node(v))

tree.build()
hld = HeavyLightDecomposition(tree)

for _ in range(Q):
    u, v = FastIO.read_int(), FastIO.read_int()
    lca = hld.lca(Node(u), Node(v))
    FastIO.writeln(f'{lca}')