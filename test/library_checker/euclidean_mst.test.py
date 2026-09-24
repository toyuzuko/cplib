# verification-helper: PROBLEM https://judge.yosupo.jp/problem/euclidean_mst

from cplib.geometry.integer import Point, euclidean_mst
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [Point(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

for u, v in euclidean_mst(points):
    FastIO.writeln(f'{u} {v}')
