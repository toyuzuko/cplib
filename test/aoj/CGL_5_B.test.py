# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/5/CGL_5_B
# verification-helper: ERROR 1e-6

from cplib.geometry.floating import Point, minimum_enclosing_circle
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [Point(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]
circle = minimum_enclosing_circle(points)
FastIO.writeln(f'{circle.center.x:.12f} {circle.center.y:.12f} {circle.radius:.12f}')
