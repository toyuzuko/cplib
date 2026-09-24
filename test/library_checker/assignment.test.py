# verification-helper: PROBLEM https://judge.yosupo.jp/problem/assignment

from cplib.graph.matching import BipartiteMinimumWeightMaximumMatching
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = [list(FastIO.read_ints(N)) for _ in range(N)]

matching_solver = BipartiteMinimumWeightMaximumMatching(N, N)

for i in range(N):
    for j in range(N):
        matching_solver.add_edge(i, j, A[i][j])

result = matching_solver.solve()

FastIO.writeln(f'{result.weight}')

res = [0] * N

for u, v in result.edges:
    res[u] = v

FastIO.writeln(' '.join(map(str, res)))
