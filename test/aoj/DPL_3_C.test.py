# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/3/DPL_3_C

from cplib.sequence.histogram import largest_rectangle_area
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
H = FastIO.read_ints(N)

FastIO.writeln(f'{largest_rectangle_area(H)}')
