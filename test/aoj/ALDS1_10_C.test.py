# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/10/ALDS1_10_C

from cplib.sequence.alignment import longest_common_subsequence_length
from cplib.tools.fastio import FastIO


Q = FastIO.read_int()
for _ in range(Q):
    X = FastIO.read()
    Y = FastIO.read()
    FastIO.writeln(f'{longest_common_subsequence_length(X, Y)}')
