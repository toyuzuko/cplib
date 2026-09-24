# verification-helper: PROBLEM https://judge.yosupo.jp/problem/general_matching

from cplib.graph.matching import MaximumWeightMatching, MatchingSuccess
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
M = FastIO.read_int()

solver = MaximumWeightMatching(N)

for _ in range(M):
    u, v = FastIO.read_ints(2)
    solver.add_edge(u, v, 1)

result = solver.solve()

FastIO.writeln(f'{len(result)}')

assert isinstance(result, MatchingSuccess)

for u, v in result.edges:
    FastIO.writeln(f'{u} {v}')