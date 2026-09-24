# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/5/DSL_5_B

from cplib.datastructure.cumulative import Imos2D
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
imos = Imos2D(1000, 1000)

for _ in range(N):
    x1, y1, x2, y2 = FastIO.read_ints(4)
    imos.add(y1, x1, y2, x2, 1)

FastIO.writeln(f'{max(max(row) for row in imos.build())}')
