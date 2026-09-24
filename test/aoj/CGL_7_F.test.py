# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/7/CGL_7_F

from cplib.geometry.floating import Circle, Point, sgn, tangent_points_from_point
from cplib.tools.fastio import FastIO


def normalize(x: float) -> float:
    return 0.0 if sgn(x) == 0 else x


px = FastIO.read_float()
py = FastIO.read_float()
x = FastIO.read_float()
y = FastIO.read_float()
r = FastIO.read_float()

points = tangent_points_from_point(Circle(Point(x, y), r), Point(px, py))
for point in points:
    FastIO.writeln(f'{normalize(point.x):.10f} {normalize(point.y):.10f}')
