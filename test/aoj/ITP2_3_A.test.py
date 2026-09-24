# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/3/ITP2_3_A

from cplib.tools.fastio import FastIO


A = FastIO.read_ints(3)
FastIO.writeln(f'{min(A)} {max(A)}')
