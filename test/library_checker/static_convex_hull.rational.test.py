# verification-helper: PROBLEM https://judge.yosupo.jp/problem/static_convex_hull

from cplib.geometry.rational import Point, convex_hull
from cplib.tools.fastio import FastIO


cases = FastIO.read_int()

for _ in range(cases):
    N = FastIO.read_int()
    points = [Point(*FastIO.read_ints(2)) for _ in range(N)]

    result = convex_hull(points)

    FastIO.writeln(f'{len(result)}')
    for i in result:
        FastIO.writeln(f'{points[i].x} {points[i].y}')
