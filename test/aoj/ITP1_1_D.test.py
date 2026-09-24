# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_D

from cplib.tools.fastio import FastIO


S = FastIO.read_int()
h = S // 3600
m = S // 60 % 60
s = S % 60
FastIO.writeln(f'{h}:{m}:{s}')
