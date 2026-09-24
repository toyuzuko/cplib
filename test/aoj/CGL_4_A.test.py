# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/4/CGL_4_A

from cplib.geometry.floating import Point, convex_hull
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points: list[Point] = []
for _ in range(N):
    x = FastIO.read_int()
    y = FastIO.read_int()
    points.append(Point(x, y))

hull = convex_hull(points, keep_collinear=True)
start = min(range(len(hull)), key=lambda i: (hull[i].y, hull[i].x))
hull = hull[start:] + hull[:start]

FastIO.writeln(f'{len(hull)}')
for point in hull:
    FastIO.writeln(f'{int(round(point.x))} {int(round(point.y))}')
