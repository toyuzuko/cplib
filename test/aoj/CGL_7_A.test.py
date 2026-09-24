# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/7/CGL_7_A

from cplib.geometry.floating import Circle, Point, circle_relation
from cplib.tools.fastio import FastIO


x1 = FastIO.read_float()
y1 = FastIO.read_float()
r1 = FastIO.read_float()
x2 = FastIO.read_float()
y2 = FastIO.read_float()
r2 = FastIO.read_float()

FastIO.writeln(f'{circle_relation(Circle(Point(x1, y1), r1), Circle(Point(x2, y2), r2))}')
