# verification-helper: PROBLEM https://judge.yosupo.jp/problem/sort_points_by_argument

from cplib.geometry.rational import Point, argsort
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [Point(*FastIO.read_ints(2)) for _ in range(N)]

sorted_points = argsort(points)

for p in sorted_points:
    FastIO.writeln(f'{p.x.num} {p.y.num}')