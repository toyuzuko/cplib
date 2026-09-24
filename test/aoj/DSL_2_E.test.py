# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/2/DSL_2_E

from cplib.datastructure.fenwicktree import RangeAddPointGet
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)

bit = RangeAddPointGet(N)

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        s, t, x = FastIO.read_ints(3)
        bit.range_add(s - 1, t, x)
    else:
        i = FastIO.read_int()
        FastIO.writeln(f'{bit.get(i - 1)}')
