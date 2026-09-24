# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/5/CGL_5_A

from cplib.geometry.floating import Point, closest_pair_distance
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points: list[Point] = []
for _ in range(N):
    x = FastIO.read_float()
    y = FastIO.read_float()
    points.append(Point(x, y))

FastIO.writeln(f'{closest_pair_distance(points):.10f}')
