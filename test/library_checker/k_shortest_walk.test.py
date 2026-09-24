# verification-helper: PROBLEM https://judge.yosupo.jp/problem/k_shortest_walk

from cplib.graph.base import Node, Weight
from cplib.graph.core import Graph
from cplib.graph.walk import k_shortest_walk
from cplib.tools.fastio import FastIO


N, M, S, T, K = FastIO.read_ints(5)
graph = Graph(N, is_directed=True)

for _ in range(M):
    u, v, w = FastIO.read_ints(3)
    graph.add_edge(Node(u), Node(v), Weight(w))

ans = k_shortest_walk(graph, Node(S), Node(T), K)
for i in range(K):
    FastIO.writeln(f'{ans[i] if i < len(ans) else -1}')
