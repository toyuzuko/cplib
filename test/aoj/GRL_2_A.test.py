# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/2/GRL_2_A

from cplib.graph import Graph, Node, Weight, minimum_spanning_tree
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
graph = Graph(V)

for _ in range(E):
    s, t, w = FastIO.read_ints(3)
    graph.add_edge(Node(s), Node(t), Weight(w))

result = minimum_spanning_tree(graph)
FastIO.writeln(f'{result.weight}')
