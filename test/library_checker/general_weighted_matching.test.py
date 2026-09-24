# verification-helper: PROBLEM https://judge.yosupo.jp/problem/general_weighted_matching

from cplib.graph.matching import MaximumWeightMatching, MatchingSuccess
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
M = FastIO.read_int()

solver = MaximumWeightMatching(N)

for _ in range(M):
    u, v, w = FastIO.read_ints(3)
    solver.add_edge(u, v, w)

result = solver.solve()

assert isinstance(result, MatchingSuccess)

FastIO.writeln(f'{len(result)} {result.weight}')

for u, v in result.edges:
    FastIO.writeln(f'{u} {v}')