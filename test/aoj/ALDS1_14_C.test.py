# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/14/ALDS1_14_C

from cplib.string.hashing import find_2d_pattern
from cplib.tools.fastio import FastIO


H, W = FastIO.read_ints(2)
S = [FastIO.read() for _ in range(H)]
R, C = FastIO.read_ints(2)
P = [FastIO.read() for _ in range(R)]

for i, j in find_2d_pattern(S, P):
    FastIO.writeln(f'{i} {j}')
