# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/1/GRL_1_A

from cplib.graph import Graph, Node, Weight
from cplib.graph import dijkstra
from cplib.tools.fastio import FastIO


V, E, r = FastIO.read_ints(3)
graph = Graph(V, is_directed=True)

for _ in range(E):
    s, t, d = FastIO.read_ints(3)
    graph.add_edge(Node(s), Node(t), Weight(d))

dist = dijkstra(graph, Node(r))

for d in dist:
    FastIO.writeln('INF' if d == Graph.dst_inf else f'{d}')
