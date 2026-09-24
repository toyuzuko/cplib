# verification-helper: PROBLEM https://judge.yosupo.jp/problem/minimum_enclosing_circle

from cplib.geometry.integer import Point, minimum_enclosing_circle
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [Point(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

is_boundary = minimum_enclosing_circle(points)

FastIO.writeln(''.join('1' if is_boundary[i] else '0' for i in range(N)))