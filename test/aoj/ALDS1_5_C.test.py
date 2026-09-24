# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/5/ALDS1_5_C

from cplib.geometry.floating import Point, koch_curve_points
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = koch_curve_points(Point(0.0, 0.0), Point(100.0, 0.0), N)

for point in points:
    FastIO.writeln(f'{point.x:.8f} {point.y:.8f}')
