# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/4/ITP1_4_A
# verification-helper: ERROR 1e-6

from cplib.tools.fastio import FastIO


a, b = FastIO.read_ints(2)
FastIO.writeln(f'{a // b} {a % b} {a / b:.10f}')
