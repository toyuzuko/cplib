# verification-helper: PROBLEM https://judge.yosupo.jp/problem/two_sat

from cplib.algorithm.sat import TwoSatSolver
from cplib.tools.fastio import FastIO


# DIMACS standard format

FastIO.read() # p
FastIO.read() # cnf

N, M = FastIO.read_ints(2)

solver = TwoSatSolver(N)

for _ in range(M):
    a, b = FastIO.read_ints(2)
    solver.add_clause(abs(a) - 1, a > 0, abs(b) - 1, b > 0)
    FastIO.read() # Read the trailing 0

result = solver.solve()

if result.satisfiable:
    FastIO.writeln('s SATISFIABLE')
    assert result.assignment is not None
    res = [i + 1 if result.assignment[i] else -(i + 1) for i in range(N)]
    FastIO.writeln(f'v {" ".join(map(str, res))} 0')

else:
    FastIO.writeln('s UNSATISFIABLE')
