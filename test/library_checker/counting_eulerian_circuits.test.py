# verification-helper: PROBLEM https://judge.yosupo.jp/problem/counting_eulerian_circuits

from cplib.graph import Graph, Node, best_theorem
from cplib.tools.fastio import FastIO


MOD = 998244353

N, M =FastIO.read_ints(2)
graph = Graph(N, is_directed = True, connectivity_check=True)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    graph.add_edge(Node(u), Node(v))

print(best_theorem(graph, MOD))