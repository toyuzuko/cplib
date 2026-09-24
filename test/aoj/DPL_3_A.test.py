# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/3/DPL_3_A

from cplib.sequence.grid import largest_square_area_in_grid
from cplib.tools.fastio import FastIO


H, W = FastIO.read_ints(2)
grid = [FastIO.read_ints(W) for _ in range(H)]

FastIO.writeln(f'{largest_square_area_in_grid(grid)}')
