# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/12/ALDS1_12_B

from cplib.graph.base import Node, Weight
from cplib.graph.core import Graph
from cplib.graph.shortest import dijkstra
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
graph = Graph(N, is_directed=True)

for _ in range(N):
    u = FastIO.read_int()
    k = FastIO.read_int()
    for _ in range(k):
        v = FastIO.read_int()
        c = FastIO.read_int()
        graph.add_edge(Node(u), Node(v), Weight(c))

dist = dijkstra(graph, Node(0))
for i, d in enumerate(dist):
    FastIO.writeln(f'{i} {d}')
