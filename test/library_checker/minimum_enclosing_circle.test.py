# verification-helper: PROBLEM https://judge.yosupo.jp/problem/minimum_enclosing_circle

from cplib.geometry.rational import Point, minimum_enclosing_circle
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [Point(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

circle = minimum_enclosing_circle(points)

res: list[str] = []

for p in points:
    if circle.on_circle(p):
        res.append('1')
    else:
        res.append('0')

FastIO.writeln(''.join(res))