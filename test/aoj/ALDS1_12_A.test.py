# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/12/ALDS1_12_A

from cplib.graph.base import Node, Weight
from cplib.graph.core import Graph
from cplib.graph.spanning import minimum_spanning_tree
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
graph = Graph(N)

for i in range(N):
    for j in range(N):
        c = FastIO.read_int()
        if i < j and c != -1:
            graph.add_edge(Node(i), Node(j), Weight(c))

FastIO.writeln(f'{minimum_spanning_tree(graph).weight}')
