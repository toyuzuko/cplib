# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/5/ITP2_5_D

from cplib.sequence.permutation import next_permutation
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = list(range(1, N + 1))

while True:
    FastIO.writeln(' '.join(map(str, A)))
    if not next_permutation(A):
        break
