# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/1/CGL_1_C

from cplib.geometry.floating import CLOCKWISE, COUNTER_CLOCKWISE, ONLINE_BACK, ONLINE_FRONT, ccw
from cplib.geometry.floating import Point
from cplib.tools.fastio import FastIO


x1 = FastIO.read_float()
y1 = FastIO.read_float()
x2 = FastIO.read_float()
y2 = FastIO.read_float()
p1 = Point(x1, y1)
p2 = Point(x2, y2)

Q = FastIO.read_int()
for _ in range(Q):
    x = FastIO.read_float()
    y = FastIO.read_float()
    result = ccw(p1, p2, Point(x, y))
    if result == COUNTER_CLOCKWISE:
        FastIO.writeln('COUNTER_CLOCKWISE')
    elif result == CLOCKWISE:
        FastIO.writeln('CLOCKWISE')
    elif result == ONLINE_BACK:
        FastIO.writeln('ONLINE_BACK')
    elif result == ONLINE_FRONT:
        FastIO.writeln('ONLINE_FRONT')
    else:
        FastIO.writeln('ON_SEGMENT')
