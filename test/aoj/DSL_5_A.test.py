# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/5/DSL_5_A

from cplib.datastructure.cumulative import Imos1D
from cplib.tools.fastio import FastIO


N, T = FastIO.read_ints(2)
imos = Imos1D(T)

for _ in range(N):
    l, r = FastIO.read_ints(2)
    imos.add(l, r, 1)

FastIO.writeln(f'{max(imos.build())}')
