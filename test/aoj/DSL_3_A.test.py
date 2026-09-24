# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/3/DSL_3_A

from cplib.sequence.window import minimum_subarray_length_with_sum_at_least_nonnegative
from cplib.tools.fastio import FastIO


N, S = FastIO.read_ints(2)
A = FastIO.read_ints(N)

FastIO.writeln(f'{minimum_subarray_length_with_sum_at_least_nonnegative(A, S)}')
