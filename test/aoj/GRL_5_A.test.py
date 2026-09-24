# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/5/GRL_5_A

from cplib.graph.base import Node, Weight
from cplib.graph.core import Tree
from cplib.graph.tree import tree_diameter
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
tree = Tree(N)

for _ in range(N - 1):
    s, t, w = FastIO.read_ints(3)
    tree.add_edge(Node(s), Node(t), Weight(w))

result = tree_diameter(tree)
FastIO.writeln(f'{result.distance}')
