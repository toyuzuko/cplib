# verification-helper: PROBLEM https://judge.yosupo.jp/problem/connected_components_of_complement_graph

from cplib.tools.fastio import FastIO
from cplib.graph import Graph, Node, complement_connected_components


N, M = FastIO.read_ints(2)

graph = Graph(N, is_directed=False)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    graph.add_edge(Node(u), Node(v))

n, comp = complement_connected_components(graph)

res: list[list[int]] = [[] for _ in range(n)]

for i, c in enumerate(comp):
    res[c].append(i)

FastIO.writeln(f'{n}')

for comp in res:
    FastIO.writeln(f'{len(comp)} ' + ' '.join(map(str, comp)))