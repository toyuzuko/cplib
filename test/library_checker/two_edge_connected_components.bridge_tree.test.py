# verification-helper: PROBLEM https://judge.yosupo.jp/problem/two_edge_connected_components

from cplib.graph.lowlink import bridge_tree
from cplib.graph import Graph, Node
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
graph = Graph(N, is_directed=False)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    graph.add_edge(Node(u), Node(v))

components = [sorted(map(int, comp)) for comp in bridge_tree(graph).components]
components.sort()

FastIO.writeln(f'{len(components)}')

for comp in components:
    FastIO.writeln(f'{len(comp)} ' + ' '.join(map(str, comp)))
