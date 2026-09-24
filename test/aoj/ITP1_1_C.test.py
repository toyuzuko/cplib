# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_C

from cplib.tools.fastio import FastIO


a, b = FastIO.read_ints(2)
FastIO.writeln(f'{a * b} {2 * (a + b)}')
