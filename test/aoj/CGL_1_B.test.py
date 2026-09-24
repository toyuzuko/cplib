# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/1/CGL_1_B

from cplib.geometry.floating import Line, Point, reflection
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
    p = reflection(line, Point(x, y))
    FastIO.writeln(f'{p.x:.10f} {p.y:.10f}')
