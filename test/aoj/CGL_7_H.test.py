# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/7/CGL_7_H
# verification-helper: ERROR 1e-5

from cplib.geometry.floating import Circle, Point, circle_polygon_intersection_area
from cplib.tools.fastio import FastIO


n = FastIO.read_int()
r = FastIO.read_int()
polygon = [Point(FastIO.read_int(), FastIO.read_int()) for _ in range(n)]
area = circle_polygon_intersection_area(Circle(Point(0, 0), r), polygon)
FastIO.writeln(f'{area:.12f}')
