# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/3/DSL_3_C

from cplib.sequence.window import count_subarrays_with_sum_at_most_nonnegative
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)
A = FastIO.read_ints(N)
queries = FastIO.read_ints(Q)

for x in queries:
    FastIO.writeln(f'{count_subarrays_with_sum_at_most_nonnegative(A, x)}')
