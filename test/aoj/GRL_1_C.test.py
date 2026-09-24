# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/1/GRL_1_C

from cplib.graph import Graph, Node, Weight
from cplib.graph import warshall_floyd
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
graph = Graph(V, is_directed=True)

for _ in range(E):
    s, t, d = FastIO.read_ints(3)
    graph.add_edge(Node(s), Node(t), Weight(d))

dist = warshall_floyd(graph)

if any(dist[v][v] < 0 for v in range(V)):
    FastIO.writeln('NEGATIVE CYCLE')
else:
    for row in dist:
        FastIO.writeln(' '.join('INF' if d == Graph.dst_inf else str(d) for d in row))
