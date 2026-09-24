# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/9/ITP2_9_A

from cplib.algorithm.sort import sorted_set_union
from cplib.tools.fastio import FastIO

N = FastIO.read_int()
A = FastIO.read_ints(N)
M = FastIO.read_int()
B = FastIO.read_ints(M)

for x in sorted_set_union(A, B):
    FastIO.writeln(f'{x}')
