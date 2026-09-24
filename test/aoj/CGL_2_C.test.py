# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/2/CGL_2_C

from cplib.geometry.floating import Point, Segment, cross_point
from cplib.tools.fastio import FastIO


Q = FastIO.read_int()
for _ in range(Q):
    x1 = FastIO.read_float()
    y1 = FastIO.read_float()
    x2 = FastIO.read_float()
    y2 = FastIO.read_float()
    x3 = FastIO.read_float()
    y3 = FastIO.read_float()
    x4 = FastIO.read_float()
    y4 = FastIO.read_float()
    s1 = Segment(Point(x1, y1), Point(x2, y2))
    s2 = Segment(Point(x3, y3), Point(x4, y4))
    p = cross_point(s1, s2)
    FastIO.writeln(f'{p.x:.10f} {p.y:.10f}')
