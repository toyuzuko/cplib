# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/3/CGL_3_C

from cplib.geometry.floating import Point, contains_point_in_polygon
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points: list[Point] = []
for _ in range(N):
    x = FastIO.read_float()
    y = FastIO.read_float()
    points.append(Point(x, y))

Q = FastIO.read_int()
for _ in range(Q):
    x = FastIO.read_float()
    y = FastIO.read_float()
    FastIO.writeln(f'{contains_point_in_polygon(points, Point(x, y))}')
