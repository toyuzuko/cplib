# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/5/ALDS1_5_D

from cplib.sequence.permutation import count_inversions
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = FastIO.read_ints(N)

FastIO.writeln(f'{count_inversions(A)}')
