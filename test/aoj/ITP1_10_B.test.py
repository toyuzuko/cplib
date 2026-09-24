# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/10/ITP1_10_B
# verification-helper: ERROR 1e-6

from math import pi, sin, cos, sqrt

from cplib.tools.fastio import FastIO


a = FastIO.read_float()
b = FastIO.read_float()
C = FastIO.read_float() * pi / 180.0
area = a * b * sin(C) * 0.5
c = sqrt(a * a + b * b - 2.0 * a * b * cos(C))
FastIO.writeln(f'{area:.10f}')
FastIO.writeln(f'{a + b + c:.10f}')
FastIO.writeln(f'{2.0 * area / a:.10f}')
