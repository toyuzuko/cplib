# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/11/ALDS1_11_C

from cplib.graph import Graph, Node
from cplib.graph import bfs
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
graph = Graph(N, is_directed=True)

for _ in range(N):
    u = FastIO.read_int() - 1
    k = FastIO.read_int()
    for v in FastIO.read_ints(k):
        graph.add_edge(Node(u), Node(v - 1))

dist = bfs(graph, Node(0))

for v, d in enumerate(dist, 1):
    FastIO.writeln(f'{v} {d if d != Graph.dst_inf else -1}')
