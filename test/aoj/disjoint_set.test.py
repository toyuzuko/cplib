# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/1/DSL_1_A

from cplib.datastructure.dsu import DisjointSetUnion
from cplib.tools.fastio import FastIO

N = FastIO.read_int()
Q = FastIO.read_int()

dsu = DisjointSetUnion(N)

for _ in range(Q):
    com = FastIO.read_int()
    x = FastIO.read_int()
    y = FastIO.read_int()
    if com == 0:
        dsu.merge(x, y)
    else:
        if dsu.same(x, y):
            FastIO.writeln('1')
        else:
            FastIO.writeln('0')
