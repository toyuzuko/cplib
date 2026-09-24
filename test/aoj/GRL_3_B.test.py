# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/3/GRL_3_B

from cplib.graph import Graph, Node, lowlink
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
graph = Graph(V)

for _ in range(E):
    s, t = FastIO.read_ints(2)
    graph.add_edge(Node(s), Node(t))

result = lowlink(graph)
bridges: list[tuple[int, int]] = []
for edge_index in result.bridges:
    u, v = graph.edges[edge_index]
    if u > v:
        u, v = v, u
    bridges.append((u, v))
bridges.sort()

for u, v in bridges:
    FastIO.writeln(f'{u} {v}')
