# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/3/DSL_3_B

from cplib.sequence.window import minimum_window_covering_multiset
from cplib.tools.fastio import FastIO


N, K = FastIO.read_ints(2)
A = FastIO.read_ints(N)

FastIO.writeln(f'{minimum_window_covering_multiset(A, range(1, K + 1))}')
