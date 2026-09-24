# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/1/CGL_1_A

from cplib.geometry.floating import Line, Point, projection
from cplib.tools.fastio import FastIO


x1 = FastIO.read_float()
y1 = FastIO.read_float()
x2 = FastIO.read_float()
y2 = FastIO.read_float()
line = Line(Point(x1, y1), Point(x2, y2))

Q = FastIO.read_int()
for _ in range(Q):
    x = FastIO.read_float()
    y = FastIO.read_float()
    p = projection(line, Point(x, y))
    FastIO.writeln(f'{p.x:.10f} {p.y:.10f}')
