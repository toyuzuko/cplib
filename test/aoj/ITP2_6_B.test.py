# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/6/ITP2_6_B

from cplib.algorithm.sort import includes_sorted
from cplib.tools.fastio import FastIO

N = FastIO.read_int()
A = FastIO.read_ints(N)
M = FastIO.read_int()
B = FastIO.read_ints(M)

FastIO.writeln('1' if includes_sorted(A, B) else '0')
