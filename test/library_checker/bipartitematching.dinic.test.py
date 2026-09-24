# verification-helper: PROBLEM https://judge.yosupo.jp/problem/bipartitematching

from cplib.graph.flow import Node, BipartiteMatching
from cplib.tools.fastio import FastIO


L, R, M = FastIO.read_ints(3)

matching_solver = BipartiteMatching(L, R)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    matching_solver.add_edge(Node(u), Node(v))

result = matching_solver.solve()

FastIO.writeln(f'{result.weight}')

for u, v in result.edges:
    FastIO.writeln(f'{u} {v}')