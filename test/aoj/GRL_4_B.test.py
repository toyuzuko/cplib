# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/4/GRL_4_B

from cplib.graph import Graph, Node, topological_sort
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
graph = Graph(V, is_directed=True)

for _ in range(E):
    s, t = FastIO.read_ints(2)
    graph.add_edge(Node(s), Node(t))

for v in topological_sort(graph):
    FastIO.writeln(f'{v}')
