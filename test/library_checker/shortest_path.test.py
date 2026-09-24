# verification-helper: PROBLEM https://judge.yosupo.jp/problem/shortest_path

from cplib.graph import Graph, shortest_path, Node, Weight
from cplib.tools.fastio import FastIO


N, M, s, t = FastIO.read_ints(4)
G = Graph(N, is_directed = True)

for _ in range(M):
    u, v, w = FastIO.read_ints(3)
    G.add_edge(Node(u), Node(v), Weight(w))

try:
    result = shortest_path(G, Node(s), Node(t))
    FastIO.writeln(f'{result.distance} {len(result.path) - 1}')
    for u, v in zip(result.path, result.path[1:]):
        FastIO.writeln(f'{u} {v}')

except ValueError:
    FastIO.writeln('-1')
