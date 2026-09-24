# verification-helper: PROBLEM https://judge.yosupo.jp/problem/shortest_path

from cplib.graph.base import Node, Weight
from cplib.graph.core import Graph
from cplib.graph.shortest import radix_dijkstra_with_prev
from cplib.tools.fastio import FastIO


N, M, s, t = FastIO.read_ints(4)
G = Graph(N, is_directed=True)

for _ in range(M):
    u, v, w = FastIO.read_ints(3)
    G.add_edge(Node(u), Node(v), Weight(w))

dist, prev = radix_dijkstra_with_prev(G, Node(s))
if dist[t] == Graph.dst_inf:
    FastIO.writeln('-1')
else:
    path: list[Node] = []
    cur = Node(t)
    while cur != -1:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    FastIO.writeln(f'{dist[t]} {len(path) - 1}')
    for u, v in zip(path, path[1:]):
        FastIO.writeln(f'{u} {v}')
