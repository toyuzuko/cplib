# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/7/DPL/1/DPL_1_D

from cplib.sequence.subseq import longest_increasing_subsequence
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
A = [FastIO.read_int() for _ in range(N)]

FastIO.writeln(f'{len(longest_increasing_subsequence(A))}')
