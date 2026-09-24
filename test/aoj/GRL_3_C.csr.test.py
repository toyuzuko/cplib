# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/3/GRL_3_C

from cplib.graph import CSRGraph, Node, strongly_connected_components_csr
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
edges: list[tuple[Node, Node]] = []

for _ in range(E):
    s, t = FastIO.read_ints(2)
    edges.append((Node(s), Node(t)))

graph = CSRGraph(V, edges, is_directed=True)
result = strongly_connected_components_csr(graph)

Q = FastIO.read_int()
for _ in range(Q):
    u, v = FastIO.read_ints(2)
    FastIO.writeln('1' if result.group[u] == result.group[v] else '0')
