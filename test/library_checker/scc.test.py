# verification-helper: PROBLEM https://judge.yosupo.jp/problem/scc

from cplib.graph import Graph, Node, strongly_connected_components
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)

G = Graph(N, is_directed=True)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    G.add_edge(Node(u), Node(v))

n, scc = strongly_connected_components(G)

res: list[list[int]] = [[] for _ in range(n)]

for i, comp in enumerate(scc):
    res[comp].append(i)

FastIO.writeln(f'{len(res)}')

for comp in res:
    FastIO.writeln(f'{len(comp)} ' + ' '.join(map(str, comp)))
