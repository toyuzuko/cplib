# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/3/CGL_3_A

from cplib.geometry.floating import Point, polygon_area
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points: list[Point] = []
for _ in range(N):
    x = FastIO.read_float()
    y = FastIO.read_float()
    points.append(Point(x, y))

FastIO.writeln(f'{polygon_area(points):.1f}')
