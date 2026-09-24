# verification-helper: PROBLEM https://judge.yosupo.jp/problem/eulerian_trail_undirected

from cplib.graph import Graph, Node, eulerian_trail
from cplib.tools.fastio import FastIO


T = FastIO.read_int()

for _ in range(T):
    N, M = FastIO.read_ints(2)
    graph = Graph(N, is_directed = False)

    for _ in range(M):
        u, v = FastIO.read_ints(2)
        graph.add_edge(Node(u), Node(v))

    exists, path_v, path_e = eulerian_trail(graph)

    if exists:
        FastIO.writeln('Yes')
        FastIO.writeln(' '.join(str(v) for v in path_v))
        FastIO.writeln(' '.join(str(e) for e in path_e))
    else:
        FastIO.writeln('No')