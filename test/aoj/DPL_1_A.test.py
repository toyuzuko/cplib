# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/1/DPL_1_A

from cplib.algorithm.dp import minimum_coin_count
from cplib.tools.fastio import FastIO


N, M = FastIO.read_ints(2)
C = FastIO.read_ints(M)

FastIO.writeln(f'{minimum_coin_count(C, N)}')
