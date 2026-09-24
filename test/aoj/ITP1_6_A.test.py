# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/6/ITP1_6_A

from cplib.tools.fastio import FastIO


n = FastIO.read_int()
A = FastIO.read_ints(n)
FastIO.writeln(' '.join(map(str, reversed(A))))
