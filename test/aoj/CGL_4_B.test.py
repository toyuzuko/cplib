# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/4/CGL_4_B

from cplib.geometry.floating import Point, convex_polygon_diameter
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points: list[Point] = []
for _ in range(N):
    x = FastIO.read_float()
    y = FastIO.read_float()
    points.append(Point(x, y))

_, _, dist2 = convex_polygon_diameter(points)
FastIO.writeln(f'{dist2 ** 0.5:.12f}')
