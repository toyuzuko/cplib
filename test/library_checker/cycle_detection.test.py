# verification-helper: PROBLEM https://judge.yosupo.jp/problem/cycle_detection

from cplib.graph import Graph, Node, cycle_detection
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
graph = Graph(N, is_directed = True)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    graph.add_edge(Node(u), Node(v))

result = cycle_detection(graph)

if result.found:
    FastIO.writeln(f'{result.length}')
    for e in result.edges:
        FastIO.writeln(f'{e}')

else:
    FastIO.writeln('-1')