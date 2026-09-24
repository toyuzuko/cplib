# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/6/ALDS1_6_B

from cplib.algorithm.sort import partition
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

B, q = partition(A)
FastIO.writeln(' '.join(f'[{x}]' if i == q else str(x) for i, x in enumerate(B)))
