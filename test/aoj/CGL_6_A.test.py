# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/6/CGL_6_A

from cplib.geometry.integer import Point, Segment, count_manhattan_intersections
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
segments: list[Segment] = []
for _ in range(N):
    x1 = FastIO.read_int()
    y1 = FastIO.read_int()
    x2 = FastIO.read_int()
    y2 = FastIO.read_int()
    segments.append(Segment(Point(x1, y1), Point(x2, y2)))

FastIO.writeln(f'{count_manhattan_intersections(segments)}')
