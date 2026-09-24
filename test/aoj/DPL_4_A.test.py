# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/4/DPL_4_A

from cplib.mathematics.combinatorics import count_four_sum
from cplib.tools.fastio import FastIO


N, V = FastIO.read_ints(2)
A = list(FastIO.read_ints(N))
B = list(FastIO.read_ints(N))
C = list(FastIO.read_ints(N))
D = list(FastIO.read_ints(N))

FastIO.writeln(f'{count_four_sum(A, B, C, D, V)}')
