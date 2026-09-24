# verification-helper: PROBLEM https://judge.yosupo.jp/problem/furthest_pair

from cplib.geometry.integer import Point, furthest_points
from cplib.tools.fastio import FastIO


cases = FastIO.read_int()

for _ in range(cases):
    N = FastIO.read_int()
    points = [Point(*FastIO.read_ints(2)) for _ in range(N)]
    i, j = furthest_points(points)

    FastIO.writeln(f"{i} {j}")
