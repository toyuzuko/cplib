# verification-helper: PROBLEM https://judge.yosupo.jp/problem/minimum_steiner_tree

from cplib.graph import Graph, minimum_steiner_tree
from cplib.graph.base import Node, Weight
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
M = FastIO.read_int()

graph = Graph(N, is_directed = False)

for _ in range(M):
    u, v, w = FastIO.read_ints(3)
    graph.add_edge(Node(u), Node(v), Weight(w))

K = FastIO.read_int()

X = [Node(FastIO.read_int()) for _ in range(K)]

mst_edges, mst_weight = minimum_steiner_tree(graph, X)

FastIO.writeln(f'{mst_weight} {len(mst_edges)}')
FastIO.writeln(' '.join(map(str, mst_edges)))
