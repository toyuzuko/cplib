# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/5/ITP2_5_C

from cplib.sequence.permutation import next_permutation, prev_permutation
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = list(FastIO.read_ints(N))
prev_A = A[:]
next_A = A[:]

if prev_permutation(prev_A):
    FastIO.writeln(' '.join(map(str, prev_A)))
FastIO.writeln(' '.join(map(str, A)))
if next_permutation(next_A):
    FastIO.writeln(' '.join(map(str, next_A)))
