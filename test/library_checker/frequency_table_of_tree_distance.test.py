# verification-helper: PROBLEM https://judge.yosupo.jp/problem/frequency_table_of_tree_distance

from cplib.graph.base import Node
from cplib.graph.core import Tree
from cplib.graph.tree import tree_distance_frequency_table
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
tree = Tree(N)

for _ in range(N - 1):
    a, b = FastIO.read_ints(2)
    tree.add_edge(Node(a), Node(b))

answer = tree_distance_frequency_table(tree)
FastIO.writeln(' '.join(map(str, answer[1:])))
