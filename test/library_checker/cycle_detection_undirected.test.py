# verification-helper: PROBLEM https://judge.yosupo.jp/problem/cycle_detection_undirected

from cplib.graph import Graph, Node, cycle_detection
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
graph = Graph(N, is_directed = False)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    graph.add_edge(Node(u), Node(v))

result = cycle_detection(graph)

if result.found:
    FastIO.writeln(f'{result.length}')
    FastIO.writeln(' '.join(str(v) for v in result.nodes))
    FastIO.writeln(' '.join(str(e) for e in result.edges))

else:
    FastIO.writeln('-1')
