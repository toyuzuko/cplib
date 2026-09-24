# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/4/ITP1_4_B
# verification-helper: ERROR 1e-6

from math import pi

from cplib.tools.fastio import FastIO


r = FastIO.read_float()
FastIO.writeln(f'{pi * r * r:.10f} {2.0 * pi * r:.10f}')
