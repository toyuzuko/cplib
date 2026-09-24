# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/10/ITP1_10_D
# verification-helper: ERROR 1e-6

from cplib.tools.fastio import FastIO


n = FastIO.read_int()
x = FastIO.read_ints(n)
y = FastIO.read_ints(n)
d = [abs(a - b) for a, b in zip(x, y)]
FastIO.writeln(f'{sum(d):.10f}')
FastIO.writeln(f'{sum(v ** 2 for v in d) ** 0.5:.10f}')
FastIO.writeln(f'{sum(v ** 3 for v in d) ** (1.0 / 3.0):.10f}')
FastIO.writeln(f'{max(d):.10f}')
