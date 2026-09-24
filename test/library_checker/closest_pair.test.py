# verification-helper: PROBLEM https://judge.yosupo.jp/problem/closest_pair

from cplib.geometry.integer import Point, closest_points
from cplib.tools.fastio import FastIO


cases = FastIO.read_int()

for _ in range(cases):
    N = FastIO.read_int()
    points = [Point(*FastIO.read_ints(2)) for _ in range(N)]
    i, j = closest_points(points)
    FastIO.writeln(f"{i} {j}")