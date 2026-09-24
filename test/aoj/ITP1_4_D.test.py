# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/4/ITP1_4_D

from cplib.tools.fastio import FastIO


n = FastIO.read_int()
A = FastIO.read_ints(n)
FastIO.writeln(f'{min(A)} {max(A)} {sum(A)}')
