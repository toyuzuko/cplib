# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/5/GRL_5_B

from cplib.graph.base import Node, Weight
from cplib.graph.core import Tree
from cplib.graph.tree import tree_diameter
from cplib.graph.treedecomp import HeavyLightDecomposition
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
tree = Tree(N)

for _ in range(N - 1):
    s, t, w = FastIO.read_ints(3)
    tree.add_edge(Node(s), Node(t), Weight(w))

diameter = tree_diameter(tree)
tree.build()
hld = HeavyLightDecomposition(tree)

for v in range(N):
    dist = max(hld.dist(Node(v), diameter.start), hld.dist(Node(v), diameter.end))
    FastIO.writeln(f'{dist}')
