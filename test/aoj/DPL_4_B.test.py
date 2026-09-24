# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/4/DPL_4_B

from cplib.mathematics.combinatorics import count_subset_sums_with_size_in_range
from cplib.tools.fastio import FastIO


N, K, L, R = FastIO.read_ints(4)
A = list(FastIO.read_ints(N))

FastIO.writeln(f'{count_subset_sums_with_size_in_range(A, K, L, R)}')
