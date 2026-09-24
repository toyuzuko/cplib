# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/3/GRL_3_C

from cplib.graph import Graph, Node, strongly_connected_components
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
graph = Graph(V, is_directed=True)

for _ in range(E):
    s, t = FastIO.read_ints(2)
    graph.add_edge(Node(s), Node(t))

result = strongly_connected_components(graph)

Q = FastIO.read_int()
for _ in range(Q):
    u, v = FastIO.read_ints(2)
    FastIO.writeln('1' if result.group[u] == result.group[v] else '0')
