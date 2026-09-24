# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/5/ALDS1_5_A

from cplib.mathematics.combinatorics import count_all_subset_sums
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = list(FastIO.read_ints(N))
Q = FastIO.read_int()
M = FastIO.read_ints(Q)

counts = count_all_subset_sums(A, max(M))
for m in M:
    FastIO.writeln('yes' if counts[m] else 'no')
