# verification-helper: PROBLEM https://judge.yosupo.jp/problem/manhattanmst

from cplib.geometry.integer import Point, manhattan_mst
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points = [Point(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

edges, total = manhattan_mst(points)
FastIO.writeln(f'{total}')
for u, v in edges:
    FastIO.writeln(f'{u} {v}')
