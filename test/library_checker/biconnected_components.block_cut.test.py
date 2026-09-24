# verification-helper: PROBLEM https://judge.yosupo.jp/problem/biconnected_components

from cplib.graph.lowlink import block_cut_tree
from cplib.graph import Graph, Node
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
graph = Graph(N, is_directed=False)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    graph.add_edge(Node(u), Node(v))

components = block_cut_tree(graph).components
components.sort()

FastIO.writeln(f'{len(components)}')
for comp in components:
    FastIO.writeln(f'{len(comp)} ' + ' '.join(map(str, comp)))
