# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/2/GRL_2_B

from cplib.graph import Graph, Node, Weight, directed_minimum_spanning_tree
from cplib.tools.fastio import FastIO


V, E, r = FastIO.read_ints(3)
graph = Graph(V, is_directed=True)

for _ in range(E):
    s, t, w = FastIO.read_ints(3)
    graph.add_edge(Node(s), Node(t), Weight(w))

result = directed_minimum_spanning_tree(graph, Node(r))
FastIO.writeln(f'{result.weight}')
