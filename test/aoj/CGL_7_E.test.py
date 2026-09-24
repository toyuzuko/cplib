# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/7/CGL_7_E

from cplib.geometry.floating import Circle, Point, circle_circle_cross_points
from cplib.tools.fastio import FastIO


x1 = FastIO.read_float()
y1 = FastIO.read_float()
r1 = FastIO.read_float()
x2 = FastIO.read_float()
y2 = FastIO.read_float()
r2 = FastIO.read_float()

p1, p2 = circle_circle_cross_points(Circle(Point(x1, y1), r1), Circle(Point(x2, y2), r2))
FastIO.writeln(f'{p1.x:.8f} {p1.y:.8f} {p2.x:.8f} {p2.y:.8f}')
