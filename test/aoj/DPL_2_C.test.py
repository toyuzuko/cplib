# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/2/DPL_2_C

from cplib.graph import bitonic_tsp
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
points: list[tuple[float, float]] = [(FastIO.read_int(), FastIO.read_int()) for _ in range(N)]

FastIO.writeln(f'{bitonic_tsp(points):.8f}')
