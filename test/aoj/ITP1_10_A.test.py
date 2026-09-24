# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/10/ITP1_10_A
# verification-helper: ERROR 1e-6

from math import hypot

from cplib.tools.fastio import FastIO


x1 = FastIO.read_float()
y1 = FastIO.read_float()
x2 = FastIO.read_float()
y2 = FastIO.read_float()
FastIO.writeln(f'{hypot(x1 - x2, y1 - y2):.10f}')
