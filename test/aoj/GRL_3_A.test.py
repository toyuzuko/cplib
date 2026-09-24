# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/5/GRL/3/GRL_3_A

from cplib.graph import Graph, Node, lowlink
from cplib.tools.fastio import FastIO


V, E = FastIO.read_ints(2)
graph = Graph(V)

for _ in range(E):
    s, t = FastIO.read_ints(2)
    graph.add_edge(Node(s), Node(t))

result = lowlink(graph)
for v in result.articulation_points:
    FastIO.writeln(f'{v}')
