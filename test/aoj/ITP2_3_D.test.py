# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/3/ITP2_3_D

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)
M = FastIO.read_int()
B = FastIO.read_ints(M)

FastIO.writeln('1' if A < B else '0')
