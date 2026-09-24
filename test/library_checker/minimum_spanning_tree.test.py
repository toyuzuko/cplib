# verification-helper: PROBLEM https://judge.yosupo.jp/problem/minimum_spanning_tree

from cplib.graph import Graph, minimum_spanning_tree, Node, Weight
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
G = Graph(N, is_directed = False)

for _ in range(M):
    u, v, w = FastIO.read_ints(3)
    G.add_edge(Node(u), Node(v), Weight(w))

mst_edges, mst_weight = minimum_spanning_tree(G)

FastIO.writeln(f'{mst_weight}')
FastIO.writeln(' '.join(map(str, mst_edges)))