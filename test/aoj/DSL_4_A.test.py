# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/4/DSL_4_A

from cplib.datastructure.range2d import static_rectangle_union_area
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
rectangles = [(FastIO.read_int(), FastIO.read_int(), FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

FastIO.writeln(f'{static_rectangle_union_area(rectangles)}')
