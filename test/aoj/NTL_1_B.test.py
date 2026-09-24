# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/6/NTL/1/NTL_1_B

from cplib.tools.fastio import FastIO


MOD = 1_000_000_007
m, n = FastIO.read_ints(2)

FastIO.writeln(f'{pow(m, n, MOD)}')
