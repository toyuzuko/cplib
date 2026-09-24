# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/5/ITP2_5_A

from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [FastIO.read_ints(2) for _ in range(N)]
points.sort()

for x, y in points:
    FastIO.writeln(f'{x} {y}')
