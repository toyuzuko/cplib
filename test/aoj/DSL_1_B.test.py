# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/1/DSL_1_B

from cplib.datastructure.dsu import WeightedDSU
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
Q = FastIO.read_int()

dsu = WeightedDSU(N)

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        x, y, z = FastIO.read_ints(3)
        dsu.merge(x, y, z)
    else:
        x, y = FastIO.read_ints(2)
        if dsu.same(x, y):
            FastIO.writeln(f'{dsu.diff(x, y)}')
        else:
            FastIO.writeln('?')
