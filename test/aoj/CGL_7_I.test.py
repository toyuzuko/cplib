# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/7/CGL_7_I
# verification-helper: ERROR 1e-6

from cplib.geometry.floating import Circle, Point, circle_circle_intersection_area
from cplib.tools.fastio import FastIO


x1 = FastIO.read_int()
y1 = FastIO.read_int()
r1 = FastIO.read_int()
x2 = FastIO.read_int()
y2 = FastIO.read_int()
r2 = FastIO.read_int()
area = circle_circle_intersection_area(Circle(Point(x1, y1), r1), Circle(Point(x2, y2), r2))
FastIO.writeln(f'{area:.20f}')
