# verification-helper: PROBLEM https://judge.yosupo.jp/problem/counting_spanning_tree_directed

from cplib.graph import Graph, kirchhoff_theorem, Node


MOD = 998244353

N, M, r = map(int, input().split())
graph = Graph(N, is_directed = True)

for _ in range(M):
    u, v = map(int, input().split())
    graph.add_edge(Node(u), Node(v))

print(kirchhoff_theorem(graph, root = Node(r), mod = MOD))