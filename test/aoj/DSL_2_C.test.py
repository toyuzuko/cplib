# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/2/DSL_2_C

from cplib.datastructure.range2d import KDTree2D
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

tree = KDTree2D(points)

Q = FastIO.read_int()

for _ in range(Q):
    sx, tx, sy, ty = FastIO.read_ints(4)
    indices = tree.rectangle_indices(sx, sy, tx + 1, ty + 1)
    indices.sort()
    for i in indices:
        FastIO.writeln(f'{i}')
    FastIO.writeln('')
