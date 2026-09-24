# verification-helper: PROBLEM https://judge.yosupo.jp/problem/convex_layers

from cplib.geometry.integer import Point, convex_layers
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [Point(*FastIO.read_ints(2)) for _ in range(N)]

answer = convex_layers(points)
for value in answer:
    FastIO.writeln(f'{value}')
