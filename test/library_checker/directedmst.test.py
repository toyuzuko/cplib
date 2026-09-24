# verification-helper: PROBLEM https://judge.yosupo.jp/problem/directedmst

from cplib.graph import Graph, Node, Weight, directed_minimum_spanning_tree
from cplib.tools.fastio import FastIO


N, M, S = FastIO.read_ints(3)
G = Graph(N, is_directed = True)

for _ in range(M):
    u, v, w = FastIO.read_ints(3)
    G.add_edge(Node(u), Node(v), Weight(w))

mst_edges, mst_weight = directed_minimum_spanning_tree(G, Node(S))

par = list(range(N))

for e in mst_edges:
    u, v = G.edges[e] # u -> v
    par[v] = u

FastIO.writeln(f'{mst_weight}')
FastIO.writeln(' '.join(map(str, par)))