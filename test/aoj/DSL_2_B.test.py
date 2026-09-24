# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/2/DSL_2_B

from cplib.datastructure.fenwicktree import FenwickTree
from cplib.tools.fastio import FastIO


N, Q = FastIO.read_ints(2)

bit = FenwickTree(N)

for _ in range(Q):
    com, x, y = FastIO.read_ints(3)
    if com == 0:
        bit.add(x - 1, y)
    else:
        FastIO.writeln(f'{bit.range_sum(x - 1, y)}')
