# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/2/CGL_2_D

from cplib.geometry.floating import Point, Segment, distance_ss
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
    FastIO.writeln(f'{distance_ss(s1, s2):.10f}')
