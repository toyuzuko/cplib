# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/2/CGL_2_A

from cplib.geometry.floating import Point, Segment, is_orthogonal, is_parallel
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
    if is_parallel(s1, s2):
        FastIO.writeln('2')
    elif is_orthogonal(s1, s2):
        FastIO.writeln('1')
    else:
        FastIO.writeln('0')
