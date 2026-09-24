# verification-helper: PROBLEM https://judge.yosupo.jp/problem/counting_spanning_tree_undirected

from cplib.graph import Graph, kirchhoff_theorem, Node


MOD = 998244353

N, M = map(int, input().split())
graph = Graph(N, is_directed = False)

for _ in range(M):
    u, v = map(int, input().split())
    graph.add_edge(Node(u), Node(v))

print(kirchhoff_theorem(graph, mod = MOD))