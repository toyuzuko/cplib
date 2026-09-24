# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/7/CGL_7_D

from cplib.geometry.floating import Circle, Line, Point, circle_line_cross_points
from cplib.tools.fastio import FastIO


x = FastIO.read_float()
y = FastIO.read_float()
r = FastIO.read_float()
circle = Circle(Point(x, y), r)

Q = FastIO.read_int()
for _ in range(Q):
    x1 = FastIO.read_float()
    y1 = FastIO.read_float()
    x2 = FastIO.read_float()
    y2 = FastIO.read_float()
    p1, p2 = circle_line_cross_points(circle, Line(Point(x1, y1), Point(x2, y2)))
    FastIO.writeln(f'{p1.x:.8f} {p1.y:.8f} {p2.x:.8f} {p2.y:.8f}')
