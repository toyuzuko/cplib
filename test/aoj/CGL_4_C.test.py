# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/4/CGL_4_C

from cplib.geometry.floating import Line, Point, convex_cut, polygon_area
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points: list[Point] = []
for _ in range(N):
    x = FastIO.read_float()
    y = FastIO.read_float()
    points.append(Point(x, y))

Q = FastIO.read_int()
for _ in range(Q):
    x1 = FastIO.read_float()
    y1 = FastIO.read_float()
    x2 = FastIO.read_float()
    y2 = FastIO.read_float()
    cut = convex_cut(points, Line(Point(x1, y1), Point(x2, y2)))
    FastIO.writeln(f'{polygon_area(cut):.8f}')
