# verification-helper: PROBLEM https://judge.yosupo.jp/problem/tree_diameter

from cplib.graph.base import Node, Weight
from cplib.graph.core import Tree
from cplib.graph.tree import tree_diameter
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
tree = Tree(N)

for _ in range(N - 1):
    u, v, w = FastIO.read_ints(3)
    tree.add_edge(Node(u), Node(v), Weight(w))

result = tree_diameter(tree)
FastIO.writeln(f'{result.distance} {len(result.path)}')
FastIO.writeln(' '.join(map(str, result.path)))
