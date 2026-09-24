# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/7/CGL_7_C
# verification-helper: ERROR 1e-6

from cplib.geometry.floating import Point, sgn, triangle_circumcircle
from cplib.tools.fastio import FastIO


def normalize(x: float) -> float:
    return 0.0 if sgn(x) == 0 else x


a = Point(FastIO.read_float(), FastIO.read_float())
b = Point(FastIO.read_float(), FastIO.read_float())
c = Point(FastIO.read_float(), FastIO.read_float())

circle = triangle_circumcircle(a, b, c)
FastIO.writeln(f'{normalize(circle.center.x):.20f} {normalize(circle.center.y):.20f} {normalize(circle.radius):.20f}')
