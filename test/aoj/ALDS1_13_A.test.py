# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/13/ALDS1_13_A

from cplib.algorithm.search import solve_n_queens
from cplib.tools.fastio import FastIO


K = FastIO.read_int()
fixed = [(FastIO.read_int(), FastIO.read_int()) for _ in range(K)]

placement = solve_n_queens(8, fixed)
assert placement is not None

for c in placement:
    row = ['.'] * 8
    row[c] = 'Q'
    FastIO.writeln(''.join(row))
